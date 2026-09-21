$env:PATH = "C:\ProgramData\Anaconda3\Library\bin;C:\ProgramData\Anaconda3\DLLs;" + $env:PATH
.\venv\Scripts\Activate.ps1
python manage.py runserver
