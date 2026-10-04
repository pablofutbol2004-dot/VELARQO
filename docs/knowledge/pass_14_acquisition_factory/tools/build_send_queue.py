#!/usr/bin/env python3
import csv, sys, uuid, datetime

ACCEPT={'valid'}

def truth(v): return str(v or '').strip().lower() in {'1','true','yes','y'}

def main(src,dst,campaign='launch01'):
    with open(src,newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    out=[]; seen=set()
    for r in rows:
        if not truth(r.get('icp_pass')): continue
        if str(r.get('send_allowed','')).lower()!='true': continue
        if truth(r.get('suppressed')): continue
        if (r.get('verification_status') or '').lower() not in ACCEPT: continue
        if not r.get('contact_id') or not r.get('company_id'): continue
        cohort=r.get('cohort_id') or 'unassigned'
        step='1'; idem=f"{r['company_id']}|{r['contact_id']}|{campaign}|{step}"
        if idem in seen: continue
        seen.add(idem)
        out.append({
            'queue_id':str(uuid.uuid4()),'campaign_id':campaign,'cohort_id':cohort,
            'company_id':r['company_id'],'contact_id':r['contact_id'],'sequence_step':step,
            'scheduled_at':r.get('scheduled_at') or '', 'sender_mailbox':r.get('sender_mailbox') or '',
            'template_version':r.get('template_version') or '', 'idempotency_key':idem,'state':'READY_TO_SEND'
        })
    fields=['queue_id','campaign_id','cohort_id','company_id','contact_id','sequence_step','scheduled_at','sender_mailbox','template_version','idempotency_key','state']
    with open(dst,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out)
    print(f'ready={len(out)}')

if __name__=='__main__':
    if len(sys.argv)<3: raise SystemExit('usage: build_send_queue.py input.csv output.csv [campaign_id]')
    main(sys.argv[1],sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'launch01')
