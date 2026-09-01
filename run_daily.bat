@echo off
rem Prism daily issue - run the full pipeline and log output.
cd /d C:\Users\zackp\Projects\prism
set PYTHONIOENCODING=utf-8
python pipeline.py all >> daily.log 2>&1
echo [%date% %time%] done >> daily.log
