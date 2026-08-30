# ID-Agent - контрольная точка

Дата проверки: 30.08.2026
Ветка: `develop`
Текущая контрольная точка: `f1bd3bf` - `Prevent AI engineering confirmation`

## Состояние репозитория

- Основная рабочая ветка: `develop`.
- GitHub: `https://github.com/shmel146177-stack/ID-Agent.git`
- Последний подтвержденный коммит: `f1bd3bf7f2df05dcf2ed16bf0a0f883da4b55b94`.
- Коммит отправлен в `origin/develop`.
- Рабочее дерево после push было чистым.

## Регрессионная проверка

Полный набор тестов:

`275 passed, 1 skipped`

Пропущенный тест связан с невозможностью создания симлинков в текущей Windows-среде и не является ошибкой ID-Agent.

`git diff --check` ошибок не выявляет.

Предупреждения LF/CRLF для Windows допустимы.

## GitHub Actions

Автоматический pytest настроен в:

`.github/workflows/tests.yml`

Используется:

- `windows-latest`
- Python `3.14`
- установка из `requirements.txt`
- `python -m pytest -q`
- запуск при push и pull request в `develop`
- `actions/checkout@v7`
- `actions/setup-python@v7`

Первоначальный запуск через раздел GitHub **Действия** был успешным.

## Подтвержденная функциональность

- сканирование PDF через PyMuPDF;
- OCR Tesseract `rus+eng`;
- классификация документов;
- анализ страниц и комплектности;
- анализ ведомости рабочих чертежей;
- карточка проекта;
- учебный режим;
- АОСР;
- журнал скрытых работ;
- генерация DOCX и Excel;
- ZIP-пакет проекта;
- `package_manifest.json`;
- реестр сопроводительных документов;
- разделы 04-06;
- управляемая загрузка сопроводительных документов;
- повторный анализ после загрузки;
- проверка соответствия документа разделу;
- обнаружение конфликтов маршрутизации;
- защита от перезаписи;
- потоковая загрузка;
- лимит файла 512 MiB;
- HTTP 413 при превышении лимита;
- удаление частичного файла при ошибке;
- безопасная общая загрузка `/projects/{project_name}/upload`;
- защита `.env` от попадания в Git.

## Реальный цикл 04-06

Учебный проект:

`Реальный_объект`

Определено 8 требований.

### 04 Исполнительные схемы

- `grounding_executive_scheme`
- `cable_entry_executive_scheme`
- `supports_executive_scheme`

### 05 Протоколы и испытания

- `grounding_resistance_protocol`
- `cable_test_protocol`

### 06 Паспорта и сертификаты

- `grounding_quality_documents`
- `cable_quality_documents`
- `supports_quality_documents`

Результат:

`REQUIRED: 8`
`FOUND: 0`
`MISSING: 8`

Все 8 требований имеют статус:

`Ожидает документа`

Фактическое содержимое:

- `04_Исполнительные_схемы` - 0 файлов
- `05_Протоколы_и_испытания` - 0 файлов
- `06_Паспорта_и_сертификаты` - 0 файлов

Это корректное состояние.

Проектная документация формирует требования, но не должна автоматически считаться исполнительной схемой, протоколом или документом качества.

Положительную проверку провести после появления настоящих сопроводительных документов.

## Исправление ложного сопоставления

При реальной проверке обнаружено, что обычное слово:

`проход`

могло ошибочно удовлетворить правилу поиска документа качества для кабельных проходок.

Добавлен регрессионный тест:

`test_real_cable_quality_requirement_rejects_generic_passage_word`

Правило уточнено:

`проход` -> `проходк`

Коммит:

`bccd8d0` - `Tighten cable quality document matching`

После исправления:

`197 passed, 1 skipped`

## Старый checkpoint c735d06

`c735d06` отсутствует в текущем локальном репозитории и в GitHub.

Он не является частью текущей истории `develop`.

Восстановление не требуется.

Пункт закрыт.

## Завершенные технические задачи

Перед следующим этапом завершены:

1. Безопасная общая загрузка файлов.
2. GitHub Actions с pytest.
3. Проверка `c735d06`.
4. Проверка отрицательного реального цикла 04-06.
5. Исправление ложного совпадения по слову `проход`.
6. Полная регрессия `197 passed, 1 skipped`.

Критических технических блокеров перед следующим этапом не обнаружено.

## Следующий этап

Следующий основной этап:

**AI/OpenAI-логика ID-Agent.**

Перед реализацией определить:

- какие задачи передавать ИИ;
- какие проверки оставить детерминированному Python-коду;
- формат структурированного ответа;
- работу при недоступности API;
- хранение API-ключа;
- тесты без реальных API-запросов;
- контроль стоимости запросов;
- запрет подтверждения инженерных фактов только ответом ИИ.

ИИ должен помогать анализировать документы и формировать предложения, но не заменять инженерное подтверждение.

## Правило разработки

После каждого изменения:

1. Запустить целевые тесты.
2. Запустить `python -m pytest -q`.
3. Выполнить `git diff --check`.
4. Выполнить `git status --short`.
5. Просмотреть diff.
6. Добавлять в Git только конкретно проверенные файлы.
7. Создавать коммит только после успешных проверок.
8. Отправлять коммит в `origin/develop`.

Не использовать без необходимости:

`git add .`

`git add -A`

`git add --all`

## Резервные материалы

Старые recovery-материалы сохранены в:

`backup/checkpoint-2026-08-24/`

Сохранены:

- `ID-Agent-d547e33-next-upload-size-limit.patch`
- `ID-Agent-recovered-311f35a/ID-Agent-recovered-311f35a.bundle`

Папка `backup/` исключена из Git.

## Учебный проект

`Реальный_объект` остается учебным проектом ID-Agent.

Отсутствующий лист №8 является предупреждением и не должен блокировать разработку.

Документы проекта и результаты анализа хранятся локально в `projects/` и не отправляются в GitHub.

## AI/OpenAI status - 30.08.2026

Current stable checkpoint:

`f1bd3bf` - `Prevent AI engineering confirmation`

Regression:

`275 passed, 1 skipped`

Implemented AI foundation:

- opt-in AI document analysis;
- safe fallback when OpenAI API is unavailable;
- AI results stored separately from deterministic analysis;
- `source_filename` and unique `analysis_id`;
- persisted human review bound to `analysis_id`;
- stale review invalidation after re-analysis;
- direct `/ai/analyze` persistence and review flow;
- `AIAnalysisComparisonService`;
- comparison groups: `matches`, `conflicts`, `suggestions`;
- missing and whitespace-only deterministic values become suggestions;
- surrounding whitespace is ignored only during string comparison;
- string case remains significant;
- deterministic types are not coerced automatically;
- `requires_human_review = True`;
- `engineering_confirmation = False`;
- AI never overwrites or confirms engineering data automatically.

Next environment-improvement plan:

1. Install and configure Ruff.
2. Add Ruff to GitHub Actions.
3. Install `pytest-cov` and measure baseline coverage.
4. Configure `pre-commit`.
5. Configure Dependabot.
6. Configure CodeQL.
7. Continue development of ID-Agent AI logic.
