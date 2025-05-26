@echo off
SETLOCAL EnableDelayedExpansion

echo === CHECK PYTHON VERSION ===
python --version 2>&1 | findstr "Python 3" >nul
if errorlevel 1 (
    echo ERROR: Python 3 is required!
    pause
    exit /b 1
)
echo === PYTHON VERSION CHECKED ===

echo === LOAD ENVIRONMENT VARIABLES ===
if not exist .env (
    echo ERROR: .env file not found!
    pause
    exit /b 1
)
for /f "usebackq tokens=1,* delims==" %%A in (.env) do (
    rem Skip lines starting with #
    echo %%A | findstr /b /r /c:"#.*" >nul
    if errorlevel 1 (
        set "%%A=%%B"
    )
)
echo === LOAD ENVIRONMENT VARIABLES COMPLETELY ===

echo === CHECK POSTGRES DATABASE ===
psql --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PostgreSQL is not installed!
    pause
    exit /b 1
)
echo === POSTGRES DATABASE IS INSTALLED ===

echo === CONNECT TO DATABASE ===
set PGPASSWORD=!DATABASE_PASSWORD!
psql -U !DATABASE_USER! -c "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Cannot connect to PostgreSQL!
    echo Check PostgreSQL server and sign-in information!
    pause
    exit /b 1
)
echo === DATABASE IS READY ===

echo === UPDATE METADATA OF DATABASE ===
psql -U !DATABASE_USER! -c "ALTER DATABASE !DATABASE_NAME! REFRESH COLLATION VERSION;"
echo === UPDATE METADATA OF DATABASE COMPLETELY ===

echo === CREATE VIRTUAL ENVIRONMENT ===
if exist venv (
    rmdir /s /q venv
    timeout /t 2 /nobreak >nul
)
python -m venv venv
call venv\Scripts\activate.bat
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)
python -m pip install --upgrade pip
python -m pip install wheel setuptools
if not exist requirements.txt (
    echo ERROR: requirements.txt not found!
    pause
    exit /b 1
)
python -m pip install -r requirements.txt
echo === CREATE VIRTUAL ENVIRONMENT COMPLETELY ===

if not exist src (
    echo ERROR: src directory not found!
    pause
    exit /b 1
)
cd src
if not exist static mkdir static
if not exist media mkdir media

echo === CREATE DATABASE ===
set PGPASSWORD=!DATABASE_PASSWORD!
psql -U !DATABASE_USER! -c "DROP DATABASE IF EXISTS !DATABASE_NAME!;"
psql -U !DATABASE_USER! -c "CREATE DATABASE !DATABASE_NAME! WITH ENCODING='UTF8' TEMPLATE=template0;"
echo === CREATE DATABASE COMPLETELY ===

echo === CREATE MIGRATIONS ===
rmdir /s /q portfolio\migrations
mkdir portfolio\migrations
type nul > portfolio\migrations\__init__.py
python manage.py makemigrations
if errorlevel 1 (
    echo ERROR: Cannot create migrations
    pause
    exit /b 1
)
python manage.py migrate
if errorlevel 1 (
    echo ERROR: Cannot apply migrations
    echo Check PostgreSQL connection
    pause
    exit /b 1
)
echo === CREATE MIGRATIONS COMPLETELY ===

echo === CREATE ADMIN ACCOUNT ===
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('!admin_username!', 'admin@example.com', '!admin_password!') if not User.objects.filter(username='!admin_username!').exists() else print('Admin already exists!!!')"
echo === CREATE ADMIN ACCOUNT COMPLETELY ===

echo === RUN SERVER ===
start http://127.0.0.1:8000 || echo WARNING: Could not open browser
python manage.py runserver

ENDLOCAL