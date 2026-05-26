# NutriScan — Resolved Decisions

Архів питань, які вже були вирішені у розмові з product owner. Агенти читають це перш ніж пере-вирішувати.

---

## R-001: Pricing snapshot policy для tokens/cost (v1.1 Phase 1)

**Дата:** 2026-05-06
**Питання:** Як рахувати `cost_usd` — snapshot у БД на момент запиту чи on-the-fly з поточного прайсу?
**Рішення:** **Snapshot at request time.** Колонка `cost_usd` фіксується при INSERT і ніколи не перераховується.
**Чому:** Прайси AI-провайдерів змінюються; перерахунок «переписав би історію». Аналітика собівартості повинна бути стабільною.
**Хто прийняв:** product owner (Євгеній).

## R-002: Backfill старих 1572 записів — REJECTED

**Дата:** 2026-05-06
**Питання:** Чи дорахувати `cost_usd` для старих записів (до v1.1) хоча б за сьогоднішнім прайсом?
**Рішення:** **Ні.** Старі записи лишаються з `cost_usd = NULL` (відображаються як `—`).
**Чому:** У старих записах немає `input_tokens`/`output_tokens` у БД — рахувати не з чого. Estimate з image_size + ingredients_count = вигадка з помилкою ±50%.
**Хто прийняв:** product owner.

## R-003: Pipeline класифікація — `app`

**Дата:** 2026-05-06
**Питання:** Який Daedalus pipeline для NutriScan — `app` чи `api`?
**Рішення:** **`app`** (вже стояв у DB — лишаємо).
**Чому:** Хоч ядро = API, є web admin-панель з UX-критеріями (фільтри, drill-down, dashboard). Pipeline `app` дає design + frontend-skeleton як опціонально-світлі.
**Хто прийняв:** product owner.

## R-004: Roadmap локально, у репо

**Дата:** 2026-05-06
**Питання:** Де тримати roadmap і ідеї?
**Рішення:** У `<project>/.ai/` файлах (`roadmap.md`, `ideas.md`), коммітити в git разом з кодом.
**Чому:** Стандартна практика Daedalus brownfield-інтеграції: один source of truth поряд з кодом.
**Хто прийняв:** product owner.

## R-005: Failed-таб як заміна логам у термiналі

**Дата:** 2026-05-06
**Питання:** Як показувати failed-запити — окрема сторінка чи tab у History?
**Рішення:** **Tab у History** (Success | Failed) з повним error-text у `<details>` (summary + scrollable monospace pre).
**Чому:** Оператор не повинен ssh-итись на сервер і робити `journalctl -u nutriscan` для розбору AI-помилок. Все має бути у браузері.
**Хто прийняв:** product owner. Реалізовано у v1.0.x (commit `f5e6ecd`).

## R-006: HTTPS на проді — відкладено

**Дата:** 2026-05-06
**Питання:** Накатити Let's Encrypt на nginx?
**Рішення:** **Відкладено** (не зараз).
**Чому:** Adminку юзає тільки оператор з відомих мереж; mobile-інтеграції BroCalories теж по HTTP поки. Вирішимо разом з v1.2.
**Хто прийняв:** product owner.

## R-007: BroCalories — Android only поки що

**Дата:** 2026-05-06
**Питання:** Apple App Store?
**Рішення:** Тільки Google Play, Apple не у планах поки що.
**Хто прийняв:** product owner.

## R-008: Telegram bot — whitelist-only

**Дата:** 2026-05-06 (фактично давніше, формалізовано)
**Питання:** Чи відкривати TG-бота для всіх?
**Рішення:** **Whitelist** через `BOT_ALLOWED_USERS` у `.env`.
**Чому:** Бот для тестування і близького кола, не для масового продукту. Mass-product — це BroCalories.
**Хто прийняв:** product owner.

## R-009: Mobile-app не шле жодних auth headers

**Дата:** 2026-05-06
**Питання:** Чи реально BroCalories шле якийсь токен / API-key / X-User-Id який ми ігноруємо?
**Перевірка:** Розширили nginx `log_format analyze_debug` для `POST /analyze/` — додали `$http_authorization`, `$http_x_api_key`, `$http_x_app_id`, `$http_x_app_version`, `$http_x_user_id`, `$http_x_request_id`. Захоплено живий запит:
```
ua="Dart/3.10 (dart:io)"  auth="-"  xapikey="-"  appid="-"  userid="-"
ctype="multipart/form-data"  len=20197  status=200
```
**Висновок:** **Жодного auth header.** Голий multipart POST. Захист треба додавати з нуля у v1.1 (per-client API-key).

## R-010: Rate-limit на `/analyze/` (stop-gap до v1.1 API-key)

**Дата:** 2026-05-06
**Питання:** Що накатити негайно як захист від зловживань на відкритому `/analyze/`?
**Рішення:** nginx-level rate-limit:
- 30 req/min per IP, burst 10 (короткий сплеск ОК), `nodelay`
- Max 5 одночасних з'єднань per IP
- Перевищення → HTTP 429 + `Retry-After: 60`
- Зони описані в `/etc/nginx/conf.d/nutriscan-ratelimit.conf`, location у `/etc/nginx/sites-enabled/nutriscan.conf`
**Чому:**
- Реальні мобільні юзери — 3-5 запитів/IP/добу, ліміт ніяк не зачіпає
- TG-бот ходить через `127.0.0.1` (минаючи nginx) — теж не зачіпається
- Daily cap відкладено: nginx без redis/memcached не вміє довгі вікна. Денний обмежувач буде в v1.1 разом з per-client API-keys у БД
**Verified:** 50 паралельних POST з одного IP → 45 отримали 429, error.log: `limiting requests, excess: 10.958 by zone "analyze_rl"`.
**Хто прийняв:** product owner.

## R-011: API-token auth — 3-фаз rollout (без зламу прод-клієнтів)

**Дата:** 2026-05-06
**Питання:** Як ввести API-token на `/analyze/` і не зламати тих, хто вже сидить зі старою версією BroCalories?
**Рішення:** Триетапний rollout:
1. **Optional** — backend приймає і з токеном, і без. Без токена → лог як "anon", з токеном → tagged з `client_id`. Розробники додають токен у мобільний клієнт, релізять у Google Play.
2. **Wait** — слідкуємо в дашборді за відсотком "anon" запитів. Чекаємо поки 95%+ юзерів оновлять додаток (~1-2 тижні з Google Play release).
3. **Mandatory** — прибираємо backward-compat, без токена → 401. За тиждень до switch — попереджуючий log-only nginx rule, щоб бачити точний impact.

**Чому:** Миттєвий mandatory зламає всіх з legacy-додатком, бо update в Google Play не миттєвий. 1-2 тижні Optional — нормальний trade-off між безпекою і UX.

**Хто прийняв:** product owner.
**Reference:** DEC-007.

## R-012: Firebase project — назва і Project ID

**Дата:** 2026-05-20
**Питання:** Як називається Firebase-проєкт BroCalories і який Project ID?
**Рішення:**
- **Project name:** `CalorieTracker` (інтенціонально — це Firebase-проєкт; "BroCalories" — це бренд мобільного додатку в Google Play)
- **Project ID:** `calorietracker-a194c`
- **Service account email:** `firebase-adminsdk-fbsvc@calorietracker-a194c.iam.gserviceaccount.com`
**Хто прийняв:** product owner (доступ є, плановано згенерувати private key).

## R-013: Firestore `users/{uid}` структура (BroCalories / CalorieTracker)

**Дата:** 2026-05-20
**Підстава:** Прямий запит до Firestore через service account `nutriscan-readonly` (Cloud Datastore Viewer), приклад документа Nightman Cometh.

**Колекції в Firestore проєкту:**
- `users` — профілі юзерів (см. поля нижче)
- `meals` — записи їжі (можливо містить історію сканів NutriScan, але треба перевірити)
- `waters` — записи води
- `weights` — історія зважувань
- `ff_push_notifications`, `push_messages` — пуш-сервіси
- (FlutterFlow `ff_*` префікс → додаток на FlutterFlow, генерує Flutter код)

**Поля `users/{uid}`:**
| Поле | Тип | Призначення |
|---|---|---|
| `uid` | string | дублікат Firebase UID |
| `email` | string | дублікат з Firebase Auth |
| `display_name` | string | те саме |
| `photo_url` | string | те саме |
| `created_time` | timestamp | дата реєстрації |
| `last_active_timestamp` | timestamp | остання активність |
| `timezone` | string | "America/Chicago", "Europe/Kyiv" і т.д. |
| `gender` | string | "male" / (мабуть і інші — `female`, `other`) |
| `age` | int | вік |
| `height` | float | зріст (см якщо `is_unitSystem_metric` — true) |
| `weight` | float | вага старт |
| `current_weight` | float | поточна вага |
| `target_weight` | float | цільова вага |
| `is_unitSystem_metric` | bool | метричні чи imperial |
| `activity_level` | string | "Sedentary", "Moderately Active", "Active", "Very Active" |
| `main_goal` | string | "Maintain weight", "Lose weight", "Gain weight" |
| `carbs` | float | частка вуглеводів у macro split (0.0-1.0) |
| `proteins` | float | частка білка |
| `fats` | float | частка жирів |
| `Questionaries_was_completed` | bool | пройшов онбординг (camelCase mix — note quirk) |
| `is_plan_activated` | bool | **ймовірне джерело tier — true=paid, false=free** (Q-017) |
| `allow_notification` | bool | дозволено пуш |
| `was_water_added_today` | bool | прапор для воду-tracking |

**Використання для NutriScan:**
- v1.2.0b (поточний): тягнемо все, показуємо у `/users/<uid>` сторінці як expandable Firestore block
- v1.3 (tier-based models): використати `is_plan_activated` як tier (після підтвердження — Q-017)
- v1.x (analytics): можемо групувати юзерів за gender/age/main_goal для маркетингу

**Хто прийняв:** confirmed by direct Firestore query 2026-05-20.

## R-014: BroCalories — крос-платформа (Android + iOS), R-007 SUPERSEDED

**Дата:** 2026-05-20
**Питання:** Чи є iOS-клієнт BroCalories? (R-007 раніше казало "ні")
**Рішення:** **Є обидва.** Flutter додаток (FlutterFlow-built), випущений і в Google Play, і в Apple App Store. Це підтверджено:
1. Знахідкою юзерів з `*@privaterelay.appleid.com` (Apple Hide My Email) у Firebase Auth
2. Прямим підтвердженням від product owner (2026-05-20)
**Naслідки:**
- **R-007 SUPERSEDED** — Apple App Store вже випущений, не "не у планах"
- **Q-007 CLOSED** — питання було про "чи буде iOS", відповідь — вже є
- Документація і брифи мають згадувати обидві платформи
- При тестуванні треба врахувати iOS-специфіку (Apple Sign-In дає specific email формат, treat as normal)
**Хто прийняв:** product owner.

## R-015: HTTPS на проді — увімкнено (R-006 SUPERSEDED)

**Дата:** 2026-05-26
**Питання:** Розгорнути TLS на `nutriscan.radarme.com.ua` (раніше R-006 — відкладено)?
**Рішення:** **Так.** Let's Encrypt сертифікат отримано через `certbot --nginx --no-redirect`. **Force-redirect 80→443 НЕ ввімкнено.**

**Рольаут (аналогія R-011 для tokens):**
1. **Зараз (HTTPS optional):** працюють обидва порти — `:80` (HTTP) і `:443` (HTTPS). Старі версії мобільного, що зашиті на HTTP, **продовжують працювати без змін**. Нові версії (як випустимо) — переключають URL на `https://`.
2. **Wait (~2 тижні):** слідкуємо в nginx access-logs за відсотком HTTP vs HTTPS трафіку. Чекаємо доки 95%+ юзерів оновляться.
3. **Mandatory:** додаємо `308 Permanent Redirect` (саме 308, не 301 — 308 зберігає POST+body) для `:80 → :443`. Старі версії додатку, які не слідують редіректам на POST, отримають помилку — це форсує оновлення.

**Технічні параметри:**
- Cert: Let's Encrypt E8, expires 2026-08-24
- Auto-renew: `certbot.timer` (систамний systemd job)
- TLS config: nginx default (TLS 1.2+, modern ciphers)

**Хто прийняв:** product owner (2026-05-26).
**Reference:** R-006 (now obsolete), R-011 (rollout pattern).
