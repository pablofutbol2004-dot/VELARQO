@echo off
rem Pilot stop conditions + pending GoHighLevel do-not-disturb pushes, every
rem 15 minutes while any pilot is running (docs/delivery/WORKFLOW.md section 5).
rem Exit 2 = a pilot is paused (read data\pilot_check.log and review it), 1 = a check failed.
cd /d D:\velarqo
call scripts\wait_for_db.cmd || exit /b 1
.venv\Scripts\python.exe -m delivery.pilot check >> data\pilot_check.log 2>&1
