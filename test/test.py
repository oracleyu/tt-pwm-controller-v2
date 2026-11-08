# SPDX-License-Identifier: Apache-2.0
"""Black-box tests: same external pins for RTL, generic and final powered netlist."""
import random
from collections import Counter
from pathlib import Path
import json
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles
from cocotb.utils import get_sim_time

class Spi:
    def __init__(self,dut): self.dut=dut;self.rng=random.Random(20261108);self.frames=0
    def pins(self,sck=0,cs=1,mosi=0): self.dut.ui_in.value=sck|(cs<<1)|(mosi<<2)
    async def frame(self,payload,bits=40,half=160):
        assert len(payload)==5
        word=int.from_bytes(bytes(payload),'big');rx=0
        await Timer(self.rng.randrange(1,20),unit='ns')
        self.pins(cs=0);await Timer(200,unit='ns')
        for i in range(bits):
            bit=(word>>(39-i))&1 if i<40 else 1
            self.pins(cs=0,mosi=bit);await Timer(half,unit='ns')
            self.pins(sck=1,cs=0,mosi=bit);await Timer(1,unit='ns')
            rx=(rx<<1)|((int(self.dut.uo_out.value)>>2)&1)
            await Timer(half-1,unit='ns');self.pins(cs=0,mosi=bit)
        await Timer(200,unit='ns');self.pins();await Timer(200,unit='ns')
        self.frames+=1
        return list((rx & ((1<<40)-1)).to_bytes(5,'big'))
    async def read(self):
        r=await self.frame([0,0,0,0,0])
        assert r[0]==0xc2, f'Bad device ID/bit alignment: {r}'
        return r
    async def config(self,l,r,div,en=1):
        before=await self.read();assert not before[1]&2
        await self.frame([0xa1,l,r,div,en])
        for _ in range(160):
            s=await self.read()
            assert not s[1]&12, f'Unexpected sticky error {s}'
            if not s[1]&2 and ((s[1]^before[1])&16):
                assert s[2:]==[l,r,div] and (s[1]&1)==en,(s,l,r,div,en)
                return s
        assert False,'Configuration commit timeout'

async def tick(dut):
    await RisingEdge(dut.clk);await Timer(5,unit='ns')
    return int(dut.uo_out.value)

async def measure(dut,l,r,div,en=1):
    n=256*(div+1)
    for _ in range(n+4):
        v=await tick(dut)
        if v&128: break
    else: assert False,'No period boundary'
    hl=hr=0
    for i in range(n):
        phase=i//(div+1)
        assert (v&1)==int(en and phase<l),('left',i,phase,l,div,v)
        assert ((v>>1)&1)==int(en and phase<r),('right',i,phase,r,div,v)
        assert ((v>>4)&1)==en
        assert ((v>>5)&1)==(phase>>7)
        assert bool(v&128)==(i==0),('boundary width',i,v)
        assert int(dut.uio_out.value)==0 and int(dut.uio_oe.value)==0
        hl+=v&1;hr+=(v>>1)&1
        v=await tick(dut)
    assert v&128,'Incorrect divider/period length'
    assert hl==(l*(div+1) if en else 0)
    assert hr==(r*(div+1) if en else 0)

async def registered_monitor(dut,stats):
    # In FUNCTIONAL gate mode UNIT_DELAY is empty: permit 5 ns settling after clk.
    # The 5..15 ns quiet window must contain no PWM edge, even while SPI changes.
    while True:
        await RisingEdge(dut.clk);await Timer(5,unit='ns')
        a=int(dut.uo_out.value)&3
        await Timer(10,unit='ns')
        b=int(dut.uo_out.value)&3
        if int(dut.rst_n.value) and stats['monitor_enabled']:
            assert a==b,'PWM changed between system-clock edges'
        stats['clocks']+=1

@cocotb.test()
async def test_protocol_and_pwm(dut):
    dut.clk.value=0;dut.rst_n.value=0;dut.ena.value=1;dut.uio_in.value=0;dut.ui_in.value=2
    cocotb.start_soon(Clock(dut.clk,20,unit='ns').start())
    stats={'clocks':0,'monitor_enabled':False}
    mon=cocotb.start_soon(registered_monitor(dut,stats))
    await ClockCycles(dut.clk,5);await FallingEdge(dut.clk);dut.rst_n.value=1
    await ClockCycles(dut.clk,8);stats['monitor_enabled']=True
    spi=Spi(dut)
    initial=await spi.read()
    assert initial==[0xc2,0,0,0,1],initial
    # Early waveform demonstration, then exhaustive duty coverage.
    await spi.config(64,192,1);await measure(dut,64,192,1)
    for code in range(256):
        await spi.config(code,255-code,0)
        await measure(dut,code,255-code,0)
    for div in [1,7,255]:
        await spi.config(64,192,div);await measure(dut,64,192,div)
    await spi.config(255,255,0,0);await measure(dut,255,255,0,0)
    # A new complete frame cannot change configuration before a period boundary.
    await spi.config(31,224,255)
    while not (await tick(dut))&128: pass
    await spi.frame([0xa1,75,181,0,1])
    s=await spi.read();assert s[1]&2 and s[2:]==[31,224,255],s
    await spi.frame([0xa1,99,100,0,1])
    s=await spi.read();assert s[1]&8 and s[1]&2,s
    for _ in range(160):
        s=await spi.read()
        if not s[1]&2: break
    assert s[2:]==[75,181,0],s
    await spi.frame([0xc0,0,0,0,0]);assert not (await spi.read())[1]&12
    # Invalid/short/long/reserved commands must leave the active configuration intact.
    invalid=[([0x55,0,0,0,0],40),([0xa1,5,6,0,1],39),([0xa1,5,6,0,1],41),
             ([0xa1,5,6,0,3],40),([0,0,0,0,1],40),([0xc0,1,0,0,0],40),([0,0,0,0,0],0)]
    for frame,bits in invalid:
        await spi.frame(frame,bits=bits)
        s=await spi.read();assert s[1]&4 and not s[1]&2 and s[2:]==[75,181,0],s
        await spi.frame([0xc0,0,0,0,0]);assert not (await spi.read())[1]&12
    # Random data, asynchronously phased SCK, and slower SPI transfer.
    for _ in range(24):
        l=spi.rng.randrange(256);r=spi.rng.randrange(256);div=spi.rng.choice([0,1,3,7])
        await spi.config(l,r,div);await measure(dut,l,r,div)
    assert (await spi.frame([0,0,0,0,0],half=500))[0]==0xc2
    # ena pauses state and aborts a frame. Resume requires idle CS first.
    await FallingEdge(dut.clk);dut.ena.value=0
    for _ in range(8): assert (await tick(dut))&3==0
    await spi.frame([0xa1,1,2,0,1])
    await FallingEdge(dut.clk);dut.ena.value=1
    await ClockCycles(dut.clk,10)
    s=await spi.read();assert s[2:]==[l,r,div] and not s[1]&12,s
    # Reset during an incomplete write flushes the frame and restores safe defaults.
    spi.pins(cs=0,mosi=1);await Timer(200,unit='ns')
    for _ in range(5):
        spi.pins(sck=1,cs=0,mosi=1);await Timer(200,unit='ns')
        spi.pins(cs=0,mosi=1);await Timer(200,unit='ns')
    stats['monitor_enabled']=False
    await FallingEdge(dut.clk);await Timer(3,unit='ns');dut.rst_n.value=0
    await Timer(5,unit='ns');assert int(dut.uo_out.value)&3==0
    await ClockCycles(dut.clk,4);spi.pins();await FallingEdge(dut.clk);dut.rst_n.value=1
    await ClockCycles(dut.clk,8);stats['monitor_enabled']=True
    assert await spi.read()==[0xc2,0,0,0,1]
    await measure(dut,0,0,1,0)
    mon.cancel()
    result={'result':'PASS','checked_system_clocks':stats['clocks'],'spi_frames':spi.frames,
            'duty_codes':256,'divider_values':[0,1,7,255],'invalid_frame_cases':len(invalid),
            'random_configs':24,'simulation_ns':get_sim_time(unit='ns')}
    Path('coverage.json').write_text(json.dumps(result,indent=2)+'\n')
    dut._log.info('V2 COVERAGE %s',result)
