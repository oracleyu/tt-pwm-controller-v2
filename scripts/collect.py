"""Collect source hashes and actual final artifacts, preserving raw metrics."""
from pathlib import Path
import hashlib,json,math
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
final=root/'src/runs/tutorial/final'
result={'gds_generated':False,'tapeout_service_signoff':'NOT_PERFORMED','source_sha256':{},'final_files':[]}
for p in [*sorted((root/'src').glob('*.v')),*sorted((root/'constraints').glob('*.sdc'))]:
    result['source_sha256'][str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
if final.exists():
    for p in sorted(final.rglob('*')):
        if not p.is_file():continue
        result['final_files'].append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    result['gds_generated']=any(p.suffix=='.gds' for p in final.rglob('*'))
metrics=list((root/'src/runs/tutorial').glob('**/metrics.json'))
# Keep every step's metrics; no inference of PASS from artifact existence.
result['step_metrics']={str(p.relative_to(root)):json.loads(p.read_text()) for p in metrics}
precheck=root/'tt/precheck/reports/results.xml'
if precheck.is_file():
    cases=ET.parse(precheck).findall('.//testcase')
    result['local_precheck']={'checks':len(cases),'errors':sum(1 for c in cases if c.find('error') is not None or c.find('failure') is not None)}
    staged=root/'reports/precheck-input/tt_um_oracleyu_pwm_v2.gds'
    actual=final/'gds/tt_um_oracleyu_pwm_v2.gds'
    result['local_precheck']['input_matches_final_gds']=staged.is_file() and actual.is_file() and staged.read_bytes()==actual.read_bytes()
def sanitize(value):
    if isinstance(value,float) and not math.isfinite(value): return None
    if isinstance(value,dict): return {k:sanitize(v) for k,v in value.items()}
    if isinstance(value,list): return [sanitize(v) for v in value]
    return value
result['simulation_coverage']={p.stem:json.loads(p.read_text()) for p in sorted((root/'reports').glob('coverage-*.json'))}
result['external_status']={'hardware_test':'NOT_RUN','service_final_acceptance':'NOT_OBTAINED','manufacturing_submission':False}
result['non_finite_metrics_note']='Non-finite upstream metrics are null here; raw metric files are preserved unchanged.'
(root/'reports/artifact-manifest.json').write_text(json.dumps(sanitize(result),indent=2,allow_nan=False)+'\n')
print(f'{len(result["final_files"])} final artifacts; gds_generated={result["gds_generated"]}; service signoff NOT_PERFORMED')
