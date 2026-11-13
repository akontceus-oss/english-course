# Speak Up English

Курс разговорного английского (60 дней, Roadmap A1 → A2) как веб-приложение для iPhone.
Сайт: https://akontceus-oss.github.io/english-course/

- `src/app.src.html` — исходник приложения; `content/` — план курса и заготовленные уроки.
- `python3 tools/build.py` собирает `index.html`, `course.json`, `sw.js`, `manifest.webmanifest`.
- Прогресс хранится в localStorage на устройстве; сервис-воркер берёт свежую версию из сети и работает офлайн.
