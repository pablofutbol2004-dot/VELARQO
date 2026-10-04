@echo off
rem Daily website refresh: new emails from installers' own sites. Safe to stop and re-run.
cd /d D:\velarqo
.venv\Scripts\python.exe -m prospecting.enrichment.website_refresh --limit 1500 >> data\website_refresh.log 2>&1
