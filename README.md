# Smart City - Мониторинг на водна инфраструктура

Интелигентна система за мониторинг на водна инфраструктура с изкуствен интелект за откриване на аномалии, прогнозиране и управление.

## Функционалности

### Приложения

1. **users** - Управление на потребители
   - Custom User модел с email за вход
   - Роли: гражданин, оператор, админ, техник
   - Потребителски профил с известия

2. **dashboard** - Табло със статистика
   - Интерактивна карта с Leaflet
   - Сензори за мониторинг
   - Аномалии и инциденти в реално време
   - Chart.js графики за консумация

3. **reports** - Система за сигнали
   - Подаване на сигнали с категории
   - GPS локация и качване на снимки
   - Статус проследяване
   - Коментари и история

4. **predictions** - AI прогнози
   - Machine Learning модели за аномалии
   - Откриване на течове
   - Прогнозиране на консумация
   - Увереност и вероятност

## Технологии

- **Django 4.2** - Web framework
- **Django REST Framework** - API
- **SQLite** - База данни
- **Bootstrap 5** - Frontend
- **Chart.js** - Графики
- **Leaflet** - Интерактивна карта
- **scikit-learn** - Machine Learning
- **Celery** - Фонови задачи (опционално)

## Инсталация

### 1. Клониране на проекта

```bash
cd smart_city
```

### 2. Създаване на виртуална среда

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Инсталация на зависимостите

```bash
pip install -r requirements.txt
```

### 4. Настройка на environment променливи

```bash
cp .env.example .env
# Редактирайте .env файла с вашите настройки
```

### 5. Миграции и създаване на база данни

```bash
python manage.py migrate
```

### 6. Създаване на суперпотребител

```bash
python manage.py createsuperuser
```

### 7. Зареждане на тестови данни

```bash
python manage.py create_test_data
```

### 8. Стартиране на сървъра

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

Или ръчно:
```bash
python manage.py runserver
```

Сървърът ще стартира на http://127.0.0.1:8000/

## Тестови потребители

След зареждане на тестовите данни, можете да използвате следните акаунти:

| Роля | Имейл | Парола |
|------|-------|--------|
| Гражданин | citizen@example.com | testpass123 |
| Оператор | operator@example.com | testpass123 |
| Техник | technician@example.com | testpass123 |
| Админ | admin@example.com | testpass123 |

## Структура на проекта

```
smart_city/
├── smart_city/          # Основна конфигурация
│   ├── settings.py      # Настройки
│   ├── urls.py          # URL маршрути
│   └── ...
├── users/               # Потребители
│   ├── models.py        # User, UserProfile, Notification
│   ├── views.py         # Login, Register, Profile
│   └── ...
├── dashboard/           # Табло и статистика
│   ├── models.py        # Sensor, Anomaly, Incident
│   ├── views.py         # Dashboard, Map, Statistics
│   └── ...
├── reports/             # Система за сигнали
│   ├── models.py        # Report, ReportComment
│   ├── views.py         # Create, List, Detail
│   └── ...
├── predictions/         # AI прогнози
│   ├── ml_models.py     # ML модели
│   ├── models.py        # Prediction, PredictionModel
│   └── ...
├── api/                 # REST API
│   ├── serializers.py   # DRF сериализатори
│   ├── views.py         # API view-та
│   └── ...
├── templates/           # HTML темплейти
├── static/              # CSS, JS, изображения
├── media/               Качени файлове
├── requirements.txt     # Зависимости
├── manage.py            # Django management
├── start.bat            # Windows стартов скрипт
├── start.sh             # Linux/Mac стартов скрипт
└── README.md            # Този файл
```

## API Endpoints

### Публични

- `GET /api/stats/` - Статистика за таблото
- `GET /api/map-data/` - Данни за картата
- `GET /api/consumption/` - Данни за консумация

### Изискват автентикация

- `GET /api/users/` - Списък с потребители
- `GET /api/sensors/` - Списък със сензори
- `GET /api/anomalies/` - Списък с аномалии
- `GET /api/incidents/` - Списък с инциденти
- `GET /api/reports/` - Списък със сигнали
- `GET /api/predictions/` - Списък с прогнози

## Machine Learning

### Модели

1. **AnomalyDetector** - Isolation Forest за откриване на аномалии
2. **LeakDetector** - Random Forest за откриване на течове
3. **ConsumptionForecaster** - Gradient Boosting за прогнозиране на консумация

### Обучение

```bash
python manage.py shell
```

```python
from predictions.ml_models import train_anomaly_model
from dashboard.models import SensorReading

# Зареди данни
readings = SensorReading.objects.filter(is_anomaly=False)

# Обучи модел
detector = train_anomaly_model(readings, 'my_model')
```

## Celery (опционално)

За фонови задачи като периодична проверка за аномалии:

```bash
# Terminal 1 - Redis
redis-server

# Terminal 2 - Celery Worker
celery -A smart_city worker -l info

# Terminal 3 - Celery Beat (periodic tasks)
celery -A smart_city beat -l info
```

## Тестване

```bash
# Стартиране на тестове
python manage.py test

# Създаване на тестови данни
python manage.py create_test_data --clean
```

## Цветова схема

- **Основен червен**: #e31e24
- **Тъмен червен**: #b02a37
- **Светъл червен**: #f8d7da

## Лиценз

Този проект е с отворен код и може да се използва свободно.

## Контакти

- Email: support@smartcity.bg
- Телефон: 0700 12 345

---

**Smart City** - Интелигентен мониторинг на водна инфраструктура
