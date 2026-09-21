@echo off
set PATH=C:\ProgramData\Anaconda3\Library\bin;C:\ProgramData\Anaconda3\DLLs;%PATH%
call .\venv\Scripts\activate.bat
python manage.py runserver
pause
