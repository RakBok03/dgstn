# DGSTN - Сайт туров по Дагестану

Проект на Django для туроператора: витрина туров, фильтрация по категориям, форма заявок и уведомления в Telegram.

## Что умеет проект

- Главная страница с hero-блоком и приветственными медиа-блоками.
- Каталог туров с фильтрацией по категориям.
- Карточки туров с описанием и галереей.
- Форма заявки на тур или консультацию.
- Отправка новой заявки в Telegram.
- Админка Django для управления контентом и турами.

## Технологии

- Python 3.11+
- Django 5
- PostgreSQL 15
- Gunicorn
- WhiteNoise
- Docker / Docker Compose

## Структура проекта

```text
.
|- core/                  # настройки Django (settings, urls, wsgi)
|- tours/                 # бизнес-логика: модели, view, urls, admin, telegram service
|- backend/templates/     # html-шаблоны страниц
|- static/                # исходная статика проекта
|- static_result/         # собранная статика (collectstatic)
|- media/                 # загружаемые файлы (фото/видео)
|- docker-compose.yml
|- Dockerfile
|- requirements.txt
`- manage.py
```

## Модели данных (кратко)

- `Category` - категория тура.
- `Tour` - основной объект тура (название, описание, цена, главное фото, признак группового тура).
- `TourPhoto` - дополнительные фото тура.
- `Feedback` - заявка с формы (имя, телефон, дата, комментарий, выбранный тур).
- `HomePageSettings` - настройки hero-блока главной страницы.
- `WelcomeBlock` - медиа-блоки "Почему выбирают нас".

## Переменные окружения

Проект читает настройки из `.env`.

Обязательные для запуска:

- `SECRET_KEY`
- `DEBUG` (`True` или `False`)
- `ALLOWED_HOSTS` (через запятую)
- `DATABASE_NAME`
- `DATABASE_USER`
- `DATABASE_PASSWORD`
- `DATABASE_HOST`
- `DATABASE_PORT`

Для уведомлений в Telegram:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Пример:

```env
SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,sadruk-tour-dag.ru

DATABASE_NAME=dgstn
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=db
DATABASE_PORT=5432

TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=-1001234567890
```

## Запуск через Docker (рекомендуется)

1. Заполнить `.env` в корне проекта.
2. Убедиться, что внешняя сеть `npm_network` существует (если используете Nginx Proxy Manager).
3. Поднять сервисы:

```bash
docker-compose up -d --build
```

После запуска:

- приложение доступно на порту `8001` (`web` контейнер);
- база PostgreSQL работает в контейнере `db`.

## Инициализация Django

Выполнить миграции и сбор статики:

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

Создать администратора:

```bash
docker-compose exec web python manage.py createsuperuser
```

## Локальный запуск без Docker

1. Создать и активировать виртуальное окружение.
2. Установить зависимости:

```bash
pip install -r requirements.txt
```

3. Настроить `.env` (в этом режиме `DATABASE_HOST` указывает на ваш локальный PostgreSQL).
4. Применить миграции и запустить сервер:

```bash
python manage.py migrate
python manage.py runserver
```

## Основные URL

- `/` - главная.
- `/tours/` - список туров.
- `/feedback/` - форма заявки.
- `/about/` - страница "О нас".
- `/admin/` - админка Django.

## Администрирование контента

Через `/admin/` можно:

- создавать и редактировать категории и туры;
- загружать дополнительные фото тура;
- управлять hero-блоком главной;
- менять приветственные медиа-блоки;
- смотреть входящие заявки.

## Поток работы с заявкой

1. Пользователь отправляет форму на `/feedback/`.
2. Создается запись в `Feedback`.
3. Сервис `tours/services.py` отправляет уведомление в Telegram.
4. Пользователь видит страницу успешной отправки.

## Примечания по продакшену

- Приложение запускается через Gunicorn.
- Статика обслуживается через WhiteNoise и `STATIC_ROOT=static_result`.
- Медиа-файлы выдаются из `MEDIA_ROOT=media`.
- Для HTTPS за reverse-proxy учитываются `X-Forwarded-*` заголовки.
