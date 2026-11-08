"""Standalone educational SKY130 mapping, independent of the physical flow."""
import os
from pathlib import Path
import subprocess
os.chdir(Path(__file__).resolve().parents[1])
pdk = Path(os.environ.get('PDK_ROOT', '.pdk')).resolve()
lib = pdk / 'sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib'
assert lib.is_file(), lib
script = f'''read_liberty -lib "{lib}"
read_verilog src/project.v
synth -top tt_um_oracleyu_pwm_v2 -flatten -noabc
dfflibmap -liberty "{lib}"
abc -liberty "{lib}"
clean
check -assert
stat -liberty "{lib}"
write_verilog -noattr reports/sky130-standalone.v
write_json reports/sky130-standalone.json
'''
Path('reports/sky130-standalone.ys').write_text(script)
subprocess.run(['yowasp-yosys', '-l', 'reports/sky130-standalone.log', '-s', 'reports/sky130-standalone.ys'], check=True)
