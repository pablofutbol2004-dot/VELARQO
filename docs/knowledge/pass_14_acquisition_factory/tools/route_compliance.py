#!/usr/bin/env python3
import csv, sys

CORPORATE={'ltd','plc','llp','private-limited','private-limited-shares','private-unlimited','company','corporate'}
INDIVIDUAL={'sole-trader','sole trader','unincorporated-partnership','partnership-individual'}

def truth(v): return str(v or '').strip().lower() in {'1','true','yes','y'}

def classify(r):
    if truth(r.get('suppressed')): return ('blocked','suppressed')
    typ=(r.get('company_type') or '').strip().lower()
    if typ in INDIVIDUAL: return ('blocked','individual_subscriber_requires_reviewed_permission')
    if typ not in CORPORATE: return ('review','entity_type_uncertain')
    if not (r.get('source_url') or r.get('source_type')): return ('review','missing_contact_provenance')
    if not truth(r.get('opt_out_ready')): return ('blocked','opt_out_not_ready')
    if not truth(r.get('suppression_checked')): return ('blocked','suppression_not_checked')
    return ('allowed','corporate_subscriber_route')

def main(src,dst):
    with open(src,newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    for r in rows:
        state,reason=classify(r); r['send_allowed']= 'true' if state=='allowed' else ('false' if state=='blocked' else 'review')
        r['compliance_reason']=reason
    fields=list(rows[0].keys()) if rows else []
    with open(dst,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    from collections import Counter
    print(Counter(r['send_allowed'] for r in rows))

if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: route_compliance.py input.csv output.csv')
    main(sys.argv[1],sys.argv[2])
