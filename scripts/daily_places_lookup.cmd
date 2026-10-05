@echo off
rem Daily Places lookup: finds websites for registered window companies, inside Google's free allowance. Safe to re-run.
cd /d D:\velarqo
.venv\Scripts\python.exe -m prospecting.enrichment.places_websites --limit 30 >> data\places_lookup.log 2>&1
