@echo off
rem Daily Places town sweep: up to 20 businesses per free lookup, matched to Companies House via their own websites. Safe to re-run.
cd /d D:\velarqo
call scripts\wait_for_db.cmd || exit /b 1
.venv\Scripts\python.exe -m prospecting.enrichment.places_sweep --limit 32 >> data\places_lookup.log 2>&1
