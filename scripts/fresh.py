"""Archive a generated physical run before reproducing it from scratch."""
from pathlib import Path
from datetime import datetime, timezone
import shutil
root=Path(__file__).resolve().parents[1]
run=root/'src/runs/tutorial'
if run.exists():
    dest=root/'archives'/('tutorial-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dest.parent.mkdir(exist_ok=True)
    shutil.move(str(run),str(dest))
    print(f'Previous run archived to {dest}')
else:
    print('No previous run to archive.')
