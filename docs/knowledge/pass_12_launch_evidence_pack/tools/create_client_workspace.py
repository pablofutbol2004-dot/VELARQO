#!/usr/bin/env python3
import shutil, sys
from pathlib import Path

if len(sys.argv)<2:
    raise SystemExit('usage: create_client_workspace.py CLIENT_ID [destination_root]')
client=sys.argv[1]
dest_root=Path(sys.argv[2] if len(sys.argv)>2 else 'clients')
out=dest_root/client
if out.exists(): raise SystemExit(f'{out} already exists')
out.mkdir(parents=True)
for rel in [
 'client_gate/client1_gate.csv','data/export_audit.csv','data/contact_eligibility.csv',
 'pilot/pilot_config.json','pilot/contact_events.csv','pilot/outcome_reconciliation.csv','pilot/message_approval.csv',
 'measurement/baseline_cohort.csv','economics/unit_economics.csv','economics/billing_reconciliation.csv',
 'learning/evidence_ledger.csv','learning/decision_log.csv','learning/assumption_registry.csv']:
    src=Path(rel)
    dst=out/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
print(out)
