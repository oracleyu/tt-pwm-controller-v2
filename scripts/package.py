"""Package project and evidence without installed tools, caches or PDK binaries."""
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
out=root.parent/'tt-pwm-controller-v2-local-results.zip'
exclude={'.DS_Store','.git','archives','.venv','.pdk','.precheck-pdk','.cache','__pycache__','sim_build','node_modules'}
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(root.rglob('*')):
        if not p.is_file() or any(x in exclude for x in p.relative_to(root).parts):continue
        if p.suffix in {'.vvp','.pyc'}:continue
        z.write(p,Path(root.name)/p.relative_to(root))
print(out)
