#!/bin/bash

echo "=========================================="
echo "   Smart City - Water Infrastructure"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Създаване на виртуална среда..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Активиране на виртуалната среда..."
source venv/bin/activate

# Install requirements
echo "Инсталация на зависимостите..."
pip install -q -r requirements.txt

# Check if database exists
if [ ! -f "db.sqlite3" ]; then
    echo "Създаване на база данни..."
    python manage.py migrate
    
    echo "Създаване на суперпотребител..."
    echo "Отговорете на въпросите за създаване на админ акаунт"
    python manage.py createsuperuser
    
    echo "Зареждане на тестови данни..."
    python manage.py create_test_data
fi

# Run migrations (in case of updates)
echo "Проверка за миграции..."
python manage.py migrate

echo ""
echo "=========================================="
echo "   Стартиране на сървъра..."
echo "   http://127.0.0.1:8000/"
echo "=========================================="
echo ""

python manage.py runserver
