@echo off
chcp 65001 >nul
echo ==========================================
echo    Smart City - Water Infrastructure
echo ==========================================
echo.

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Създаване на виртуална среда...
    python -m venv venv
)

:: Activate virtual environment
echo Активиране на виртуалната среда...
call venv\Scripts\activate.bat

:: Install requirements
echo Инсталация на зависимостите...
pip install -q -r requirements.txt

:: Check if database exists
if not exist "db.sqlite3" (
    echo Създаване на база данни...
    python manage.py migrate
    
    echo Създаване на суперпотребител...
    echo Отговорете на въпросите за създаване на админ акаунт
    python manage.py createsuperuser
    
    echo Зареждане на тестови данни...
    python manage.py create_test_data
)

:: Run migrations (in case of updates)
echo Проверка за миграции...
python manage.py migrate

echo.
echo ==========================================
echo    Стартиране на сървъра...
echo    http://127.0.0.1:8000/
echo ==========================================
echo.

python manage.py runserver

pause
