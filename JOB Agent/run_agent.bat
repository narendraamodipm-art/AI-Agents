@echo off
rem Used by Windows Task Scheduler:  run_agent.bat run   or   run_agent.bat replies
cd /d "%~dp0.."
if not exist "JOB Agent\data" mkdir "JOB Agent\data"
echo ==== %date% %time% %1 >> "JOB Agent\data\agent.log"
".venv\Scripts\python.exe" "JOB Agent\agent.py" %1 >> "JOB Agent\data\agent.log" 2>&1
