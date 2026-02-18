# Социальный вишлист — что сделано, как запустить и проверить

Документ описывает все доработки проекта (аудит, хардинг, фронт, полировка) и пошаговый запуск с проверкой.

---

## Что сделано

### Бэкенд (FastAPI, PostgreSQL)

**Архитектура и слои**
- Роутеры вызывают только сервисы; логика публичного и владельческого вишлиста перенесена в `WishlistService` (`get_public_dto`, `get_with_items_for_owner`).
- Импорты приведены в порядок (без циклических, без дублирования).

**Корректность и конкуренция**
- Резервирование: частичный уникальный индекс по `(item_id) WHERE cancelled_at IS NULL` — только одна активная резервация на товар; при гонке второй запрос получает `IntegrityError`, обрабатывается и возвращает 409.
- Вклад (contribute): блокировка строки `SELECT FOR UPDATE` по товару, проверка «уже полностью собран» и «превысит цель»; при полном сборе возвращается явное сообщение «Item is already fully funded».
- Деньги: все суммы в `Decimal`, хелперы в `app/core/money.py` (`safe_sum`, `progress_percent`).

**N+1 и производительность**
- Публичный вишлист: один запрос «вишлист + items» (`get_by_share_token_with_items`), один батч сумм по item_id, один батч активных резерваций; сборка DTO в памяти.
- Добавлен индекс для одной активной резервации на товар (миграция 004).

**Безопасность и лимиты**
- CORS из конфига (`CORS_ORIGINS`).
- Валидация URL парсера товаров: только `http`/`https`, проверка через `urlparse`.
- Rate limit для публичного эндпоинта: per-IP, запросов в минуту (настраивается `RATE_LIMIT_PUBLIC_PER_MINUTE`, 0 = выключено).

**Идемпотентность вкладов**
- Заголовок `Idempotency-Key`: при одном и том же ключе + session_id + item_id возвращается сохранённый ответ 201 без повторного списания (in-memory кэш с TTL 24 ч).

**Парсер товаров (preview)**
- В ответ добавлены `preview_quality` (`"full"` | `"partial"` | `"minimal"`) и `missing_fields` (список полей, которые не удалось извлечь: title, image_url, price).

**Единый формат ошибок API**
- Все ошибки в виде `{"detail": "...", "error_code": "..."}`.
- Коды: `validation_error`, `invalid_request`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `rate_limited`, `internal_error` (описаны в OpenAPI).

**Realtime (WebSocket)**
- Рассылка событий через `BackgroundTasks` после ответа (после коммита БД).
- При падении Redis/рассылки — логирование, без падения запроса.
- Reconnect на фронте с экспоненциальным backoff (до 5 попыток).

**Демо-скрипт**
- `seed_demo.py`: создаёт пользователя, вишлист, несколько товаров и примеры вкладов; выводит публичную ссылку и логин.

**OpenAPI**
- Описание ошибок и кодов, теги по доменам, примеры ответов для ключевых эндпоинтов.

---

### Фронтенд (Next.js)

- **WebSocket**: переподключение с backoff при обрыве.
- **Загрузка/ошибки**: скелетоны на публичной странице, дашборде и редактировании; экраны ошибок с кнопкой «Try again».
- **Кнопки при мутациях**: по каждому действию (reserve / unreserve / contribute) свой pending, блокировка только нужных кнопок и подписи «Reserving…», «Adding…».
- **Защита от двойного нажатия**: при contribute не отправляется второй запрос до завершения первого.
- **Оптимистичные обновления**: резерв/отмена резерва и вклад обновляют UI сразу, при ошибке — откат.
- **Прогресс-бар**: обновляется из realtime (при событии `contribution_added` кэш обновляется без лишнего refetch).
- **Публичная страница без авторизации**: маршрут `/public/[token]` не проходит через middleware проверки auth.
- **Владелец не видит контрибьюторов**: API и схемы не отдают идентификаторы; на странице редактирования показываются только товары и цены.
- **Обработка ошибок API**: разбор `detail` (строка или массив валидации).
- **Адаптив**: отступы и типографика для мобильных.

---

## Как запустить

### 1. База данных

Нужен PostgreSQL 14+.

```bash
# Пример: создание БД (Linux/macOS)
createdb wishlist

# Или через psql
psql -U postgres -c "CREATE DATABASE wishlist;"
```

### 2. Бэкенд

В корне проекта (где `app/`, `alembic/`, `requirements.txt`):

```bash
# Виртуальное окружение
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# Зависимости (если есть requirements.txt)
pip install -r requirements.txt
# Или через pyproject.toml
pip install -e .

# Конфиг
copy .env.example .env           # Windows
# cp .env.example .env           # Linux/macOS
# Отредактировать .env: DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/wishlist

# Миграции
alembic upgrade head

# Запуск API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

После запуска:
- API: http://localhost:8000  
- Документация: http://localhost:8000/docs  
- Health: http://localhost:8000/api/health  
- Readiness (проверка БД): http://localhost:8000/api/health/ready  

### 3. Демо-данные (опционально)

В отдельном терминале, в корне проекта, с активированным `.venv`:

```bash
python seed_demo.py
```

Скрипт создаёт пользователя `demo@example.com` / `demo-password-123`, вишлист и товары с примерами вкладов и выводит в консоль:
- публичную ссылку вида `http://localhost:3000/public/<share_token>`;
- логин и пароль владельца.

Переменные окружения (или `.env`):
- `DATABASE_URL` — как у приложения (по умолчанию `postgresql+asyncpg://postgres:postgres@localhost:5432/wishlist`);
- `PUBLIC_BASE_URL` — база для ссылки (по умолчанию `http://localhost:3000`).

### 4. Фронтенд

```bash
cd frontend
cp .env.local.example .env.local
# В .env.local задать: NEXT_PUBLIC_API_URL=http://localhost:8000/api

npm install
npm run dev
```

Открыть http://localhost:3000.

- Для входа владельца: `demo@example.com` / `demo-password-123` (если выполняли `seed_demo.py`).
- Публичная ссылка из вывода `seed_demo.py` открывается без входа (reserve, contribute, realtime).

---

## Как проверить

### Тесты бэкенда

В корне проекта (где `app/`):

```bash
# Все тесты
python -m pytest tests/ -v

# Только юнит-тесты (без БД)
python -m pytest tests/test_product_parser.py tests/test_money.py tests/test_contribution_service.py tests/test_reservation_service.py tests/test_wishlist_service.py tests/test_public_dto_schema.py -v

# С БД (в т.ч. тест публичного эндпоинта 404)
set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/wishlist
python -m pytest tests/ -v
```

Ожидается: все тесты зелёные (при отсутствии БД один тест публичного эндпоинта будет пропущен).

### Ручная проверка API

1. **Health**  
   `GET http://localhost:8000/api/health` → `{"status":"ok"}`.

2. **Регистрация и логин**  
   - `POST /api/auth/register` с `{"email":"test@test.com","password":"password123"}`.  
   - `POST /api/auth/login` с теми же данными → в ответе cookies.

3. **Публичный вишлист (без auth)**  
   - Выполнить `seed_demo.py`, взять `share_token` из вывода.  
   - `GET http://localhost:8000/api/wishlists/public/<share_token>` без cookies → 200, тело с вишлистом и items (reserved, contributed_total, progress).

4. **Rate limit**  
   - Много раз подряд: `GET /api/wishlists/public/<token>` (например, >60 раз в минуту с одного IP).  
   - Ожидается 429 с `{"detail":"Too many requests","error_code":"rate_limited"}`.  
   - В `.env` можно поставить `RATE_LIMIT_PUBLIC_PER_MINUTE=3` и проверить быстрее.

5. **Идемпотентность contribute**  
   - Открыть публичную страницу в браузере, получить cookie `session_id`.  
   - `POST /api/items/<item_id>/contribute` с телом `{"amount": 5}` и заголовком `Idempotency-Key: my-key-123` дважды.  
   - Оба ответа 201 с одинаковым телом; в базе должен быть один новый вклад.

6. **Превью товара**  
   - `POST /api/items/preview` с `{"product_url": "https://example.com"}`.  
   - В ответе должны быть поля `preview_quality` и `missing_fields`.

7. **Формат ошибок**  
   - `GET /api/wishlists/public/00000000-0000-0000-0000-000000000000` → 404 с телом `{"detail":"...", "error_code":"not_found"}`.

### Проверка фронтенда

1. Войти как `demo@example.com` / `demo-password-123`, открыть вишлист, добавить товар, скопировать ссылку «Share: /public/...».
2. В режиме инкогнито (или другой браузер) открыть эту ссылку — страница должна открыться без логина.
3. На публичной странице: нажать Reserve → кнопка должна показать «Reserving…» и затем «Cancel reservation»; прогресс-бар при contribute должен обновляться (в т.ч. при открытии той же страницы в другой вкладке — realtime).
4. При отключении сети или неверном API URL — экран ошибки и кнопка «Try again».

### Сборка фронтенда

```bash
cd frontend
npm run build
```

Убедиться, что сборка проходит без ошибок.

---

## Переменные окружения (кратко)

**Бэкенд (`.env`)**  
- `DATABASE_URL` — обязательно, `postgresql+asyncpg://...`  
- `SECRET_KEY` — обязательно в проде, длинная случайная строка  
- `CORS_ORIGINS` — например `http://localhost:3000`  
- `RATE_LIMIT_PUBLIC_PER_MINUTE` — лимит для публичного эндпоинта (0 = выкл)  
- `REDIS_URL` — опционально, для WebSocket между воркерами  
- `PUBLIC_BASE_URL` — для вывода ссылки в `seed_demo.py`  

**Фронтенд (`.env.local`)**  
- `NEXT_PUBLIC_API_URL` — например `http://localhost:8000/api`  

---

## Структура проекта (актуальная)

```
wishlist/
├── app/
│   ├── api/routers/      # auth, health, items, users, wishlists, ws
│   ├── core/             # config, database, security, money
│   ├── dependencies/     # get_db, get_*_service, get_anonymous_session_id
│   ├── lib/              # idempotency
│   ├── middleware/       # rate_limit (public wishlist)
│   ├── models/           # User, Wishlist, WishItem, Reservation, Contribution
│   ├── repositories/     # слой доступа к БД
│   ├── schemas/          # Pydantic (в т.ч. errors, wish_item с preview_quality)
│   ├── services/         # бизнес-логика (wishlist, contribution, reservation, product_parser)
│   └── websocket/        # manager, events, redis_broadcast
├── frontend/             # Next.js 14, App Router
├── alembic/versions/     # миграции (в т.ч. 004 — уникальный индекс резерваций)
├── tests/
├── seed_demo.py          # демо-данные и вывод публичной ссылки
├── Dockerfile            # образ API
├── README.md
└── DEMO.md               # этот файл
```

Если что-то из шагов не срабатывает (например, порт занят или БД недоступна), проверьте логи сервера и переменные окружения.
