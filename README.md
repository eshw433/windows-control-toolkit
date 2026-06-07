# Windows Control Toolkit — v2.2 "Aurora"

<p align="center">
  <img src="https://img.shields.io/badge/version-2.2.0-blue?style=for-the-badge&color=5cd0ff" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge&color=4dd599" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/website-live-9a7dff?style=for-the-badge" alt="Website">
</p>

**Автор:** Шохлат Мурадов (Shokhlat Muradov) · Telegram: @diver5 · **Финальный проект, 2026**

**[Website](https://eshw433.github.io/windows-control-toolkit/) · [Releases](https://github.com/eshw433/windows-control-toolkit/releases) · [Issues](https://github.com/eshw433/windows-control-toolkit/issues)**

---

## Коротко

Windows Control Toolkit (WCT) — настольное приложение на **Python 3.12 + PyQt6**, которое держит под контролем две вещи, ежедневно отвлекающие пользователя Windows:

1. **Кто и куда из ваших программ ходит в сеть** — живой монитор соединений + правила фаервола + риск-скоринг + DNS-кэш.
2. **Что творится в папке «Загрузки» и в проекте** — сканер, организатор по правилам, поиск дубликатов, карантин и полный откат.

Версия **2.1 «Aurora»** — диспетчер задач, инспектор процессов, планировщик, онбординг, live-графики, светлая тема, фильтры истории, drag & drop, PDF-экспорт и полный набор тестов.

**v2.2 «Aurora»** — добавлены: менеджер автозагрузки, USB-монитор, поиск по содержимому файлов и авто-обновление. Всё локально, без облачной телеметрии.

---

## Changelog

### v2.1 (2026-05-24) — текущая версия

| # | Функция | Описание |
|---|---|---|
| 1 | **Диспетчер задач** | Полноценный диспетчер в стиле Windows: live CPU/RAM шкалы, таблица всех процессов с сортировкой по CPU, поиск, завершение задач. Работает в фоновом `QThread` — не блокирует UI |
| 2 | **Инспектор процессов** | Детальный просмотр процессов: CPU%, RAM, статус, потоки, путь к exe. Sparkline-график истории CPU для выбранного процесса. Завершение процесса. Фоновый поток |
| 3 | **Планировщик (UI)** | Страница управления периодическими задачами: добавление, запуск/остановка, удаление. Задачи: scan_downloads, backup_db, clear_cache, check_updates, export_events |
| 4 | **Welcome Screen** | Онбординг при первом запуске — 4 шага с описанием ключевых функций и точками-индикаторами. Показывается один раз, запоминается в БД |
| 5 | **Live-графики на Dashboard** | Sparkline-графики CPU% и RAM% в реальном времени (обновление каждые 3 сек). Показывает среднее значение. Данные берутся из фонового планировщика |
| 6 | **Фильтры в Истории** | Фильтрация по типу действия (move/rename/quarantine/...) и статусу (completed/failed/rolled_back) + текстовый поиск по путям |
| 7 | **Светлая тема `light`** | 6-й пресет темы: белый фон, синий акцент (#1a73e8), полная поддержка всех компонентов UI |
| 8 | **Горячие клавиши в Карантине** | `Del` = удалить выбранные, `R` = восстановить выбранные. Работают без мыши |
| 9 | **Drag & Drop в Правилах файлов** | Перетащить файл или папку на страницу → автоматически открывается диалог создания правила с заполненным расширением и путём |
| 10 | **PDF-экспорт** | `export_pdf()` в `exporter.py` через `reportlab`. Если библиотека не установлена — автоматический fallback на текстовый файл |
| 11 | **Pytest тесты** | 6 тест-файлов: `test_rule_engine`, `test_exporter`, `test_stats`, `test_text_search`, `test_format`, `test_risk`. Запуск: `pytest tests/` |
| 12 | **Секция "Все функции" в О проекте** | Полное описание всех 20 функций приложения прямо в About page с иконками и пояснениями |
| 13 | **Исправление лагов** | Process Inspector и Task Manager переведены на `QThread`. Таймеры стартуют только при открытии страницы (`showEvent`/`hideEvent`). CPU poll использует `interval=None` |

### v2.2 (2026-06-07) — новые функции

| # | Функция | Описание |
|---|---|---|
| 14 | **Startup Manager** | Управление автозагрузкой Windows: сканирование реестра (HKCU/HKLM Run, RunOnce) и папок Startup. Включение, отключение и удаление записей |
| 15 | **USB Monitor** | Мониторинг подключённых USB-накопителей через WMI и psutil. Отображение имени, буквы диска, размера и статуса |
| 16 | **File Content Search** | Полнотекстовый поиск внутри файлов (TXT, PDF, DOCX). Поиск по папке с рекурсией, превью найденных строк и номера строк |
| 17 | **Auto-updater** | Проверка обновлений через GitHub Releases API. Отображение текущей и последней версии, release notes, открытие страницы релиза в браузере |

### v2.0 "Aurora" (2026-05-16)

- 5 тёмных тем (midnight, aurora, solar, amethyst, graphite)
- Командная палитра Ctrl+K с 28+ командами
- About page: hero-блок, live-метрики, storage-шкалы, плагины, changelog
- Сетевой модуль: bandwidth-tracker, GeoIP, DNS-кэш, risk-скорер
- Файловый модуль: 16 шаблонов правил, дедупликация (двухшаговый хэш), disk hogs
- БД: 20 таблиц, WAL mode, миграции
- i18n: 380+ ключей, EN/RU/AZ
- Системный трей, автозапуск, резервное копирование, экспорт CSV/JSON

---

## Все функции

| Страница | Что делает |
|---|---|
| **Dashboard** | Сводная панель: 4 счётчика + live sparkline CPU/RAM + таблица последних событий |
| **Сетевой монитор** | Все активные TCP/UDP соединения в реальном времени: приложение, PID, IP, домен, страна, протокол |
| **Правила фаервола** | Создание/удаление правил Windows Firewall (WCT_ префикс). Блокировка по приложению, порту, протоколу |
| **Трафик** | Входящий/исходящий трафик по приложениям за день. Скорость в реальном времени |
| **Центр рисков** | Автоматическая оценка риска соединений. Цветовая индикация: низкий/средний/высокий |
| **Решения по доверию** | История решений allow/block для каждого процесса. Временные разрешения |
| **Загрузки** | Сканирование папки по правилам. Предпросмотр плана организации перед применением |
| **Правила файлов** | Создание правил: условия (расширение, имя, размер, возраст) + действия (move/rename/quarantine/delete). Drag & Drop |
| **Дубликаты** | Поиск дубликатов по SHA-256. Удаление с выбором стратегии |
| **Большие файлы** | Анализ папки: самые большие, старые, устаревшие файлы |
| **Карантин** | Безопасное хранение файлов. Откат одним кликом. Горячие клавиши Del/R |
| **История** | Журнал всех файловых операций. Фильтры по типу и статусу. Откат действий |
| **Уведомления** | Центр уведомлений всех событий системы |
| **Инспектор процессов** | Детальный просмотр процессов + sparkline CPU-истории. Завершение процесса |
| **Диспетчер задач** | Live CPU/RAM шкалы + таблица всех процессов. Завершение задач |
| **Планировщик** | Управление периодическими задачами из UI |
| **Автозагрузка** | Управление записями реестра и папками Startup. Вкл/выкл/удаление |
| **USB монитор** | Подключённые USB-накопители: имя, буква, размер, статус |
| **Поиск по файлам** | Полнотекстовый поиск в TXT, PDF, DOCX. Превью и номера строк |
| **Обновления** | Проверка релизов на GitHub, просмотр release notes, скачивание |
| **Настройки** | 6 тем, 3 языка, автозапуск, тихие часы, интервал опроса |
| **О проекте** | Системная информация, live-метрики, плагины, все функции, changelog |

---

## Что нового в 2.0 «Aurora»

**UI** | 6 готовых тем (`midnight`, `aurora`, `solar`, `amethyst`, `graphite`, `light`), общая палитра из 14 переменных, рамки и hover-состояния доведены до однородности |
**Командная палитра** | Ctrl+K → быстрый поиск по 31+ командам (навигация, диагностика, открытие папок, экспорт настроек) |
**About page** | Полностью переписана: hero-блок, лайв-метрики (CPU/RAM/процессы/uptime), сторадж-шкалы, реестр плагинов, секция шортката, MIT-лицензия и changelog (рендер встроенным Markdown-lite) |
**Системные модули** | `sysinfo`, `diagnostics` (text/json/файл), `build_info`, `updater` (GitHub Releases API), `hotkeys`, `plugins`, `usage` (локальная JSONL-телеметрия) |
**Сеть** | Bandwidth-tracker, GeoIP-таблица, реестр портов (100+), DNS-кэш, risk-скорер |
**Файлы** | 16 встроенных шаблонов правил, размер-анализ, продвинутый дедуп (двухшаговый хэш), отчёты |
**БД** | +8 таблиц поверх существующих (bandwidth, trust_decisions, dns_history, duplicate_groups, folder_profiles, rule_templates, scan_history, kv_settings), миграции в `migrations.py` |
**Память интерфейса** | Запоминаем позицию окна, последнюю страницу, историю палитры и поиска — `preferences.json` |
**Глифы и иконки** | Единый реестр UI-символов для боковой панели и кнопок |
**i18n** | 420+ ключей, 3 языка: English, Русский, Azərbaycan |

### Новые функции (v2.1)

| Функция | Описание |
|---|---|
| **Process Inspector** | Детальный просмотр процессов: CPU/RAM, статус, потоки, sparkline-история CPU, завершение процесса |
| **Task Manager** | Диспетчер задач Windows-стиль: live CPU/RAM шкалы, сортировка по CPU, завершение задач |
| **Scheduler UI** | Страница управления периодическими задачами: добавление, запуск/остановка, удаление |
| **Welcome Screen** | Онбординг при первом запуске — 4 шага с описанием возможностей |
| **Dashboard Charts** | Исторические sparkline-графики CPU% и RAM% в реальном времени |
| **History Filters** | Фильтры по типу действия и статусу + текстовый поиск |
| **Light Theme** | Светлая тема `light` — 6-я тема в пресетах |
| **Quarantine Hotkeys** | `Del` = удалить, `R` = восстановить в карантине |
| **Drag & Drop Rules** | Перетащить файл/папку на страницу File Rules для быстрого создания правила |
| **PDF Export** | `export_pdf()` в `exporter.py` (через reportlab, fallback на текст) |
| **Pytest Tests** | 6 тест-файлов: rule_engine, exporter, stats, text_search, format, risk |

### Новые функции (v2.2)

| Функция | Описание |
|---|---|
| **Startup Manager** | Управление автозагрузкой Windows: реестр (HKCU/HKLM Run, RunOnce) + папки Startup |
| **USB Monitor** | Мониторинг USB-накопителей через WMI и psutil |
| **File Content Search** | Полнотекстовый поиск в TXT, PDF, DOCX с превью и номерами строк |
| **Auto-updater** | Проверка обновлений через GitHub Releases, просмотр release notes, скачивание |

---

## Скриншоты (что увидит пользователь)

```
┌─────────────┬──────────────────────────────────────────────┐
│  WCT        │  Hero · v2.0.0 · Aurora · MIT                │
│  Aurora     │  Update status / changelog                   │
│             │                                              │
│  ▣ Dashboard│  [ open data ] [ logs ] [ qr ] [ backups ]   │
│  ⚡ Network │  [ copy diag ] [ save diag ] [ check updt ]  │
│  ⛨ Firewall│                                               │
│  ≈ Bandwidth│  System info ──── Process resources          │
│  ▲ Risk     │  OS / CPU / RAM   PID / Threads / Mem / CPU% │
│  ✓ Trust    │                                              │
│  ⤓ Downloads│  Storage ▮▮▮▮▮▮▮▯▯ DB · QR · Logs · Backups  │
│  ☰ Rules    │                                              │
│  ⧉ Dupes    │  Plugins (12 builtin)   Shortcuts            │
│  ◆ Disk hogs│  Tech stack             Links                │
│  ⛔ Quarant. │  Changelog              MIT License          │
│  ⟳ History  │                                              │
│  ✧ Notif.   │                                              │
│  ⚙ Settings │                                              │
│  ℹ About    │                                              │
│             │                                              │
│ v2.0 Aurora │                                              │
│ Ctrl·K palet│                                              │
└─────────────┴──────────────────────────────────────────────┘
```

---

## Архитектура

```
final_project/
├── README.md
├── requirements.txt
├── pyproject.toml
└── src/wct/
    ├── __init__.py            # __version__ = 2.0.0, __codename__ = Aurora
    ├── main.py                # точка входа, выбор темы по AppSettings.general.theme
    ├── app.py                 # связывает UI ↔ сервисы ↔ БД
    │
    ├── config/
    │   ├── paths.py           # data / logs / cache / plugins / exports / config / reports
    │   └── settings.py        # GeneralSettings · NetworkSettings · FilesSettings
    │
    ├── core/                  # инфраструктура без зависимости от UI
    │   ├── i18n.py            # 380+ ключей · 3 языка
    │   ├── event_bus.py       # publish/subscribe внутри процесса
    │   ├── commands.py        # Command + undo-история
    │   ├── command_palette.py # Command/CommandRegistry/populate_defaults
    │   ├── glyphs.py          # реестр UI-символов
    │   ├── preferences.py     # окно · последняя страница · фавориты
    │   ├── usage.py           # локальная JSONL-телеметрия
    │   ├── sysinfo.py         # SystemSnapshot, cpu_usage, network_interfaces …
    │   ├── diagnostics.py     # build_report → text / json / файл
    │   ├── build_info.py      # версия · кодовое имя · runtime
    │   ├── changelog.py       # ChangelogEntry · to_markdown · find
    │   ├── markdown_lite.py   # лёгкий MD → HTML без сторонних зависимостей
    │   ├── plugins.py         # PluginInfo · PluginRegistry · builtin · load_external
    │   ├── hotkeys.py         # HotkeyBinding · HotkeyManager
    │   ├── updater.py         # GitHub Releases API + сравнение версий
    │   ├── notifications.py   # центр уведомлений
    │   ├── scheduler.py       # таймеры/cron-подобные задачи
    │   ├── tray.py            # системный трей
    │   ├── autostart.py       # автозапуск через реестр Windows
    │   ├── backup.py          # резервные копии БД
    │   ├── exporter.py        # CSV / JSON экспорт
    │   ├── format.py          # числа · байты · даты
    │   ├── text_search.py     # text / regex / fuzzy
    │   ├── throttle.py        # debounce / throttle
    │   └── stats.py           # счётчики и агрегаты
    │
    ├── db/
    │   ├── database.py        # обёртка над SQLite, WAL
    │   ├── schema.sql         # 20 таблиц
    │   ├── migrations.py      # последовательные миграции схемы
    │   └── repositories.py    # 9 репозиториев CRUD
    │
    ├── modules/
    │   ├── network/
    │   │   ├── monitor.py · service.py · models.py
    │   │   ├── firewall_adapter.py · dns_resolver.py
    │   │   ├── bandwidth.py · bandwidth_service.py
    │   │   ├── dns_cache.py · geoip.py · port_registry.py
    │   │   └── risk.py · risk_scorer.py
    │   ├── files/
    │   │   ├── scanner.py · service.py · actions.py · models.py
    │   │   ├── rule_engine.py · templates.py · monitor.py
    │   │   ├── dedupe.py · dedupe_pro.py · size_analyzer.py
    │   │   └── content_search.py
    │   └── system/
    │       ├── startup_manager.py · usb_monitor.py
    │
    ├── shared/
    │   └── models.py          # общие enum/dataclass
    │
    └── ui/
        ├── main_window.py     # sidebar · 23 страницы · Ctrl+K · Ctrl+R · Ctrl+Q
        ├── theme.py           # PALETTE · PRESETS · stylesheet_for(name)
        ├── widgets/
        │   ├── stat_card.py · sparkline.py · search_box.py · progress_chip.py
        │   └── command_palette.py   # сам диалог Ctrl+K
        └── pages/
            ├── dashboard_page.py
            ├── network_page.py · firewall_rules_page.py · bandwidth_page.py
            ├── risk_page.py · trust_page.py
            ├── downloads_page.py · file_rules_page.py
            ├── duplicates_page.py · disk_hogs_page.py · quarantine_page.py
            ├── history_page.py · notifications_page.py
            ├── process_inspector_page.py · task_manager_page.py
            ├── scheduler_page.py · startup_page.py · usb_page.py
            ├── content_search_page.py · updater_page.py
            ├── settings_page.py
            └── about_page.py
```

---

## Темы

`src/wct/ui/theme.py` собирает QSS из палитры из 14 переменных. Доступно 5 пресетов:

| Имя | Акцент | Настроение |
|---|---|---|
| `midnight` (по умолчанию) | `#5cd0ff` cyan | классический тёмно-синий |
| `aurora` | `#5cd0ff` + `#9a7dff` violet glow | холодный, чуть фиолетовый |
| `solar` | `#ffb547` amber | тёплый, контрастный |
| `amethyst` | `#9a7dff` purple | пурпурный/фиолетовый |
| `graphite` | `#9aa6c0` neutral | спокойный нейтральный |

Сменить тему: `Settings → General → theme` или `AppSettings.general.theme = "aurora"`. Без перезапуска — пересоберите окно через перезаход, либо вызовите `qt_app.setStyleSheet(stylesheet_for("aurora"))`.

---

## Командная палитра (Ctrl + K)

35+ команд из коробки, сгруппированы по `Navigation`, `View`, `System`, `App`:

- `nav.*` — мгновенный переход на любую из 23 страниц
- `action.open_data` / `open_logs` / `open_quarantine` / `open_backups`
- `action.copy_diag` / `save_diag` — копировать/сохранить полный диагностический отчёт
- `action.check_updates` — проверить GitHub Releases
- `action.clear_cache` · `action.backup_db` · `action.export_settings`
- `action.open_repo` · `action.quit`
- `action.refresh` — перерисовать текущую страницу

Fuzzy-фильтр + история недавних команд (поднимаются вверх).

---

## База данных (20 таблиц)

| Группа | Таблицы |
|---|---|
| Системные | `app_events`, `notifications`, `settings`, `kv_settings`, `scan_history` |
| Сеть | `process_identities`, `network_connections`, `firewall_rules`, `trust_decisions`, `dns_history`, `bandwidth` |
| Файлы | `file_items`, `file_rules`, `rule_templates`, `file_actions`, `folder_profiles`, `duplicate_groups`, `quarantine_items` |

Включён **WAL mode**, индексы расставлены на наиболее частых выборках. Миграции версионируются в `db/migrations.py`.

---

## Стек технологий

| Что | Зачем | Версия |
|---|---|---|
| Python | основной язык | 3.12+ |
| PyQt6 | GUI | 6.6+ |
| psutil | соединения / процессы / RAM / CPU | 5.9+ |
| watchdog | мониторинг файловой системы | 4.0+ |
| pydantic | модели настроек | 2.5+ |
| loguru | логирование (ротация, retention) | 0.7+ |
| SQLite | локальная БД | встроенный |
| netsh | управление Windows Firewall | системный |

---

## Установка и запуск

pip install -r requirements.txt
python -m wct.main


Для применения правил Windows Firewall запустите от администратора. Мониторинг работает и без админских прав.

---

## Хранение данных

```
%LOCALAPPDATA%\WindowsControlToolkit\
├── wct.db                  # SQLite (20 таблиц, WAL)
├── settings.json           # GeneralSettings · NetworkSettings · FilesSettings
├── usage.jsonl             # локальная телеметрия событий
├── config/
│   └── preferences.json    # окно · последняя страница · история палитры
├── cache/                  # временные снапшоты / кэш
├── plugins/                # внешние плагины (опц.)
├── exports/                # экспорт настроек, отчётов
├── reports/                # диагностические отчёты
├── quarantine/             # карантин файлов
├── backups/                # резервные копии БД
└── logs/
    └── wct_YYYY-MM-DD.log
```

---

## Метрики проекта

| Метрика | Значение |
|---|---|
| Файлов исходного кода (`*.py`) | 100+ |
| Строк Python (без `__pycache__`) | 15 000+ |
| Таблиц в БД | 20 |
| Страниц UI | 23 |
| Команд палитры | 35+ |
| Тем (пресетов) | 6 |
| Плагинов (builtin) | 12 |
| Языков интерфейса | 3 (en / ru / az) |
| Ключей переводов | 440+ |
| Тест-файлов (pytest) | 6 |
| Модулей системы | 3 (network, files, system) |

---

## Безопасность и приватность

1. Все данные локально, в `%LOCALAPPDATA%`. **Никаких облачных вызовов, никакой телеметрии наружу.**
2. Updater опционален и обращается только к публичному GitHub Releases API — отключите, если не нужен.
3. Файлы никогда не удаляются — карантин и откат.
4. Файлы в процессе загрузки (`.crdownload`, `.part`, `.tmp`) обходятся стороной.
5. Правила фаервола создаются с префиксом `WCT_` — пользовательские правила Windows не трогаются.
6. Системные процессы (`svchost`, `lsass`, …) в белом списке.

*Шохлат Мурадов · Aurora · 2026 · Python · PyQt6 · SQLite · psutil · watchdog · pydantic · loguru*
