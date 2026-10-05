@echo off
rem Daily free-data collection (Companies House API). Safe to stop and re-run.
cd /d D:\velarqo
call scripts\wait_for_db.cmd || exit /b 1
.venv\Scripts\python.exe -m prospecting.enrichment.free_facts >> data\free_facts.log 2>&1
