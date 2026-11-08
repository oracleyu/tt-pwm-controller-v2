"""Structural audit of intentional asynchronous ingress; not an MTBF signoff."""
from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'reports/generic-netlist.json').read_text())['modules']['tt_um_oracleyu_pwm_v2']
lines=[]
for index,name in [(0,'sck_sync'),(1,'cs_sync'),(2,'mosi_sync')]:
    pin=m['ports']['ui_in']['bits'][index]
    sinks=[]
    for cell,info in m['cells'].items():
        for port,bits in info['connections'].items():
            if info['port_directions'].get(port)=='input' and pin in bits:
                sinks.append((cell,info['type'],port))
    assert len(sinks)==1 and sinks[0][2]=='D' and 'DFF' in sinks[0][1],(index,sinks)
    stages=m['netnames'][name]['bits']
    assert len(stages)==3
    assert m['cells'][sinks[0][0]]['connections']['Q']==[stages[0]]
    for a,b in zip(stages,stages[1:]):
        links=[v for v in m['cells'].values() if 'DFF' in v['type'] and v['connections'].get('D')==[a] and v['connections'].get('Q')==[b]]
        assert len(links)==1,(name,a,b)
    lines.append(f'ui_in[{index}] -> {name}[0] -> [1] -> [2]: verified; raw pin has only first-flop D fanout')
sta=root/'reports/sta-crosscheck.log'
if sta.is_file():
    text=sta.read_text()
    endpoints=re.findall(r'^\s+([\w]+/D)\s*$',text,re.M)
    nl=(root/'src/runs/tutorial/final/nl/tt_um_oracleyu_pwm_v2.nl.v').read_text()
    qnames=[]
    for endpoint in endpoints:
        cell=endpoint.split('/')[0]
        block=re.search(r'sky130_fd_sc_hd__\w+\s+'+re.escape(cell)+r'\s*\((.*?)\);',nl,re.S)
        assert block,endpoint
        q=re.search(r'\.Q\(\\?(\w+\[0\])',block[1]);assert q,endpoint
        qnames.append(q[1]);lines.append(f'Intentional STA exception {endpoint} -> {q[1]}')
    assert sorted(qnames)==sorted(['sck_sync[0]','cs_sync[0]','mosi_sync[0]']),qnames
    assert 'ACTUAL_PROPAGATED_CLOCK=1' in text
lines.append('PASS: 3 intended async SPI first-stage endpoints; no multi-bit command CDC (single-clock oversampling).')
lines.append('Metastability is not simulated; no MTBF or silicon CDC signoff claimed.')
(root/'reports/cdc-audit.txt').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
