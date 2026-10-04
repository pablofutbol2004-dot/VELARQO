#!/usr/bin/env python3
import csv, sys

def yn(v): return (v or '').strip().lower()

def score(r):
    fatal=[]
    if yn(r.get('service_fit')) != 'yes': fatal.append('service_fit')
    if yn(r.get('suppression_clear')) != 'yes': fatal.append('suppression')
    if yn(r.get('duplicate_clear')) != 'yes': fatal.append('duplicate')
    if not (r.get('email') or '').strip(): fatal.append('email')
    if not (r.get('email_source') or '').strip(): fatal.append('email_source')
    if fatal: return 0,'EXCLUDE',';'.join(fatal)
    s=0; reasons=[]
    for field, pts in [
        ('homeowner_facing',3),('quote_flow_visible',3),('decision_maker_verified',2),
        ('corporate_entity_confident',1)]:
        if yn(r.get(field))=='yes': s+=pts; reasons.append(field)
    products=(r.get('products') or '').lower()
    if any(k in products for k in ['window','door','bifold','conserv','roof']): s+=2; reasons.append('product_match')
    unknowns=sum(1 for f in ['homeowner_facing','quote_flow_visible','decision_maker_verified','corporate_entity_confident'] if yn(r.get(f)) not in ('yes','no'))
    s-=min(unknowns,2)
    band='A' if s>=9 else 'B' if s>=6 else 'C'
    return s,band,','.join(reasons)

def main(inp,out):
    with open(inp,encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    for r in rows:
        s,b,why=score(r); r['priority_score']=s; r['priority_band']=b; r['score_reason']=why
    rows.sort(key=lambda r:(r['priority_band']=='EXCLUDE',-int(r['priority_score'])))
    fields=list(rows[0].keys()) if rows else []
    for x in ['priority_score','priority_band','score_reason']:
        if x not in fields: fields.append(x)
    with open(out,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f'Wrote {len(rows)} prospects to {out}')
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: score_prospects.py input.csv output.csv')
    main(sys.argv[1],sys.argv[2])
