import sqlite3
import os
from config import Config

def get_db():
    """Получить соединение с базой данных."""
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row  # Возвращать строки как словари
    return conn

def init_db():
    """Создать все таблицы если они не существуют."""
    os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)

    conn = get_db()
    c = conn.cursor()

    # ── ПОЛЬЗОВАТЕЛИ ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            phone        TEXT    UNIQUE NOT NULL,
            full_name    TEXT    DEFAULT 'Новый пользователь',
            role         TEXT    DEFAULT 'student',  -- student | teacher
            group_name   TEXT    DEFAULT '',
            score        INTEGER DEFAULT 0,
            streak       INTEGER DEFAULT 0,
            level        TEXT    DEFAULT 'Новичок',
            created_at   TEXT    DEFAULT (datetime('now'))
        )
    ''')

    # ── SMS КОДЫ ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS sms_codes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            phone      TEXT NOT NULL,
            code       TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used       INTEGER DEFAULT 0
        )
    ''')

    # ── КУРСЫ ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT,
            section     TEXT,   -- pedagogy | it | special
            emoji       TEXT    DEFAULT '📚',
            teacher_id  INTEGER,
            FOREIGN KEY (teacher_id) REFERENCES users(id)
        )
    ''')

    # ── МОДУЛИ ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS modules (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id   INTEGER NOT NULL,
            title       TEXT    NOT NULL,
            content     TEXT,
            order_num   INTEGER DEFAULT 1,
            test_url    TEXT    DEFAULT '',
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    ''')

    # ── ЗАПИСИ НА КУРС ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id  INTEGER NOT NULL,
            enrolled_at TEXT   DEFAULT (datetime('now')),
            UNIQUE(student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (course_id)  REFERENCES courses(id)
        )
    ''')

    # ── РЕЗУЛЬТАТЫ ТЕСТОВ ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL,
            module_id   INTEGER NOT NULL,
            score       INTEGER DEFAULT 0,
            max_score   INTEGER DEFAULT 20,
            completed   INTEGER DEFAULT 0,
            completed_at TEXT   DEFAULT (datetime('now')),
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (module_id)  REFERENCES modules(id)
        )
    ''')

    # ── ПРОГРЕСС ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL,
            course_id   INTEGER NOT NULL,
            module_id   INTEGER NOT NULL,
            done        INTEGER DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (course_id)  REFERENCES courses(id),
            FOREIGN KEY (module_id)  REFERENCES modules(id)
        )
    ''')

    # ── ОТКРЫТЫЕ ОТВЕТЫ ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS open_answers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL,
            module_id   INTEGER NOT NULL,
            answer_text TEXT,
            score       INTEGER DEFAULT NULL,
            comment     TEXT    DEFAULT '',
            checked     INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (module_id)  REFERENCES modules(id)
        )
    ''')

    # ── БЕЙДЖИ ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS badges (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            name       TEXT NOT NULL,
            icon       TEXT DEFAULT '🏅',
            earned_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (student_id) REFERENCES users(id)
        )
    ''')

    # ── ВЕБИНАРЫ ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS webinars (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            course_id   INTEGER,
            teacher_id  INTEGER,
            date_time   TEXT,
            duration    INTEGER DEFAULT 90,
            platform    TEXT DEFAULT 'Google Meet',
            link        TEXT DEFAULT '#',
            section     TEXT DEFAULT 'all',
            FOREIGN KEY (course_id)  REFERENCES courses(id),
            FOREIGN KEY (teacher_id) REFERENCES users(id)
        )
    ''')

    # ── ФОРУМ ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS forum_threads (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            title      TEXT NOT NULL,
            body       TEXT,
            category   TEXT DEFAULT 'question',
            views      INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS forum_replies (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER NOT NULL,
            user_id   INTEGER NOT NULL,
            body      TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (thread_id) REFERENCES forum_threads(id),
            FOREIGN KEY (user_id)   REFERENCES users(id)
        )
    ''')

    # ── УВЕДОМЛЕНИЯ ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            text       TEXT,
            type       TEXT DEFAULT 'info',  -- info | warning | success
            is_read    INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # ── ДНЕВНИК ОБУЧЕНИЯ ──
    c.execute('''
        CREATE TABLE IF NOT EXISTS diary (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id  INTEGER,
            text       TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (student_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")


def seed_db():
    """Заполнить БД тестовыми данными."""
    conn = get_db()
    c = conn.cursor()

    # Проверяем, есть ли уже данные
    c.execute("SELECT COUNT(*) FROM courses")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    # Преподаватели
    teachers = [
        ('+998901234567', 'Алишер Каримов',    'teacher', 'Кафедра педагогики'),
        ('+998901234568', 'Нилуфар Рашидова',  'teacher', 'Кафедра педагогики'),
        ('+998901234569', 'Бобур Усманов',      'teacher', 'Кафедра IT'),
        ('+998901234570', 'Санжар Тошматов',    'teacher', 'Кафедра IT'),
        ('+998901234571', 'Дилноза Юсупова',    'teacher', 'Кафедра географии'),
    ]
    for t in teachers:
        c.execute("INSERT OR IGNORE INTO users (phone, full_name, role, group_name) VALUES (?,?,?,?)", t)

    # Курсы
    courses = [
        ('Технологии дистанционного обучения',
         'Принципы PBL, Google Classroom, геймификация и автоматические тесты.',
         'pedagogy', '🎓', 1),
        ('Педагогическая геймификация',
         'Alias, Wordle, SOYA и дебаты в учебном процессе.',
         'pedagogy', '🎮', 2),
        ('Python-разработка: Kivy, SQLite, pandas',
         'От фреймворка Kivy до работы с библиотеками SQLite и pandas.',
         'it', '🐍', 3),
        ('Основы кибербезопасности и защита данных',
         'Защита данных, моделирование угроз, игра SOYA.',
         'it', '🔐', 4),
        ('Геоинформационные системы (ГИС)',
         'Анализ пространственных данных и ГИС-инструменты.',
         'special', '🌍', 5),
    ]
    for course in courses:
        c.execute("INSERT INTO courses (title, description, section, emoji, teacher_id) VALUES (?,?,?,?,?)", course)

    # Модули для курса 1
    modules_c1 = [
        (1, 'Модуль 1. Введение в дистанционное обучение', 'Что такое ДО, история и принципы', 1, 'https://learningapps.org/watch?app=pxeia9tha24'),
        (1, 'Модуль 2. Проблемно-ориентированное обучение (PBL)', 'Принципы PBL и датская модель', 2, 'https://learningapps.org/watch?app=pxeia9tha24'),
        (1, 'Модуль 3. Геймификация и рейтинговая система', 'Alias, Wordle, лидерборд', 3, 'https://learningapps.org/watch?app=pxeia9tha24'),
    ]
    for m in modules_c1:
        c.execute("INSERT INTO modules (course_id, title, content, order_num, test_url) VALUES (?,?,?,?,?)", m)

    # Студенты
    students = [
        ('+998901111111', 'Алишер Исмоилов',  'student', '1001-23 КИ', 340),
        ('+998901111112', 'Зафар Алимов',      'student', '1001-23 КИ', 520),
        ('+998901111113', 'Нилуфар Рахимова',  'student', '1001-23 КИ', 480),
        ('+998901111114', 'Дилшод Юсупов',     'student', '1001-23 КИ', 455),
        ('+998901111115', 'Сарвар Мирзаев',    'student', '1001-23 КИ', 310),
        ('+998901111116', 'Малика Хасанова',   'student', '1001-23 КИ', 290),
    ]
    for s in students:
        c.execute("INSERT OR IGNORE INTO users (phone, full_name, role, group_name, score) VALUES (?,?,?,?,?)", s)

    conn.commit()
    conn.close()
    print("✅ Тестовые данные добавлены")
