# ЭдуПлатформа — Педагогическое программное средство

> Тема: «Значение педагогических программных средств в повышении эффективности образовательного процесса и их этапы создания»

---

## 📁 Структура проекта

```
edu-platform/
├── index.html          ← Главная страница
├── catalog.html        ← Каталог дисциплин
├── course.html         ← Страница курса
├── student.html        ← Личный кабинет студента
├── teacher.html        ← Личный кабинет преподавателя
├── stages.html         ← Этапы создания ППС
├── about.html          ← О платформе
├── forum.html          ← Форум и обсуждения
├── schedule.html       ← Расписание вебинаров
├── style.css           ← Все стили
├── script.js           ← Логика фронтенда
├── backend/
│   ├── app.py          ← Flask приложение
│   ├── config.py       ← Настройки
│   ├── models.py       ← База данных (SQLite)
│   ├── routes.py       ← API маршруты
│   └── requirements.txt
└── database/
    └── db.sqlite3      ← (создаётся автоматически)
```

---

## 🚀 Запуск

### 1. Открыть фронтенд (без бэкенда)
Просто открой `index.html` в браузере — всё работает статически.

### 2. Запустить бэкенд Flask

```bash
# Перейди в папку backend
cd backend

# Установить зависимости
pip install -r requirements.txt

# Запустить сервер
python app.py
```

Сервер запустится на: **http://127.0.0.1:5000**

### 3. Заполнить тестовыми данными
```bash
curl -X POST http://127.0.0.1:5000/api/seed
```
Или открой в браузере: http://127.0.0.1:5000/api/seed (POST запрос)

---

## 📱 Авторизация по телефону

- Вход через номер телефона (+998)
- OTP-код отправляется через Eskiz.uz
- **В режиме разработки**: код всегда `1234`

---

## 🔗 API Endpoints

| Метод | URL | Описание |
|-------|-----|----------|
| POST | /api/auth/send-otp | Отправить OTP-код |
| POST | /api/auth/verify-otp | Проверить код и войти |
| POST | /api/auth/logout | Выйти |
| GET  | /api/auth/me | Текущий пользователь |
| GET  | /api/courses | Список курсов |
| GET  | /api/courses/:id | Курс с модулями |
| POST | /api/courses/:id/enroll | Записаться |
| GET  | /api/progress | Прогресс студента |
| POST | /api/progress/complete-module | Отметить модуль |
| POST | /api/tests/submit | Сохранить результат теста |
| GET  | /api/student/dashboard | Дашборд студента |
| GET  | /api/student/leaderboard | Рейтинг группы |
| GET  | /api/teacher/group | Список студентов |
| GET  | /api/teacher/answers | Ответы для проверки |
| POST | /api/teacher/answers/:id/grade | Выставить оценку |
| GET  | /api/forum | Темы форума |
| POST | /api/forum | Создать тему |
| POST | /api/forum/:id/reply | Ответить |
| GET  | /api/webinars | Расписание |
| GET  | /api/diary | Дневник обучения |
| POST | /api/diary | Добавить запись |
| GET  | /api/health | Статус сервера |

---

## 🗄 База данных

Таблицы SQLite:
- `users` — студенты и преподаватели
- `sms_codes` — OTP-коды
- `courses` — курсы
- `modules` — модули курсов
- `enrollments` — записи на курсы
- `test_results` — результаты тестов
- `progress` — прогресс по модулям
- `open_answers` — открытые ответы
- `badges` — бейджи
- `webinars` — расписание
- `forum_threads` — темы форума
- `forum_replies` — ответы форума
- `notifications` — уведомления
- `diary` — дневник обучения

---

## 🎓 Педагогические методы

- **PBL** (Problem-Based Learning) — проблемно-ориентированное обучение
- **Геймификация** — баллы, бейджи, уровни, лидерборд
- **LearningApps** — интерактивные тесты после каждого модуля
- **Дебаты** — «Жизнь в Instagram: мотивация или депрессия?»
- **SOYA** — игра с тайными ролями для кибербезопасности
- **Дневник рефлексии** — запись мыслей после модулей

---

© 2024 ЭдуПлатформа — Университетский проект
