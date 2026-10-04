#!/usr/bin/env python3
import csv, sys
from pathlib import Path

path=Path(sys.argv[1] if len(sys.argv)>1 else 'client_gate/client1_gate.csv')
rows=list(csv.DictReader(path.open(encoding='utf-8')))
valid={'PASS','FAIL','OPEN','NOT_APPLICABLE'}
errors=[]; blockers=[]; pass_count=0
for r in rows:
    st=(r.get('status') or '').strip().upper()
    if st not in valid:
        errors.append(f"{r['gate_id']}: invalid status {st!r}")
        continue
    if st=='PASS':
        pass_count+=1
        if not (r.get('evidence_ref') or '').strip():
            errors.append(f"{r['gate_id']}: PASS requires evidence_ref")
    elif st in {'FAIL','OPEN'}:
        blockers.append(f"{r['gate_id']} [{r['group']}]: {r['requirement']} — {st}")
    elif st=='NOT_APPLICABLE':
        if (r.get('waivable') or '').strip().upper()!='YES':
            errors.append(f"{r['gate_id']}: NOT_APPLICABLE not allowed for non-waivable row")
        if not ((r.get('notes') or '').strip() or (r.get('applicability_note') or '').strip()):
            errors.append(f"{r['gate_id']}: NOT_APPLICABLE requires explanation")
print(f"Rows: {len(rows)} | PASS: {pass_count} | blockers: {len(blockers)} | validation errors: {len(errors)}")
if blockers:
    print('\nBLOCKERS')
    for x in blockers: print('-',x)
if errors:
    print('\nVALIDATION ERRORS')
    for x in errors: print('-',x)
if blockers or errors:
    print('\nNOT READY')
    sys.exit(2)
print('\nREADY FOR CANARY — gate only. Pilot config/cohort freeze still required.')
