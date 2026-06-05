from flask import request, jsonify, session
from models import get_db, seed_db
from config import Config
from datetime import datetime, timedelta
import random
import re

def register_routes(app):

    # ══════════════════════════════════
    #   АВТОРИЗАЦИЯ
    # ══════════════════════════════════

    @app.route('/api/auth/send-otp', methods=['POST'])
    def send_otp():
        """Отправить OTP-код на телефон."""
        data  = request.get_json()
        phone = data.get('phone', '').strip()

        if not phone or len(phone) < 9:
            return jsonify({'error': 'Неверный номер телефона'}), 400

        # Форматируем номер
        if not phone.startswith('+998'):
            phone = '+998' + phone

        # Генерируем код (в тесте всегда 1234)
        code = Config.TEST_OTP if app.config.get('DEBUG') else str(random.randint(1000, 9999))
        expires_at = (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

        db = get_db()
        # Удаляем старые коды
        db.execute("DELETE FROM sms_codes WHERE phone = ?", (phone,))
        db.execute(
            "INSERT INTO sms_codes (phone, code, expires_at) VALUES (?, ?, ?)",
            (phone, code, expires_at)
        )
        db.commit()
        db.close()

        # Здесь будет отправка через Eskiz.uz
        # send_sms_eskiz(phone, f"Ваш код: {code}")
        print(f"📱 SMS код для {phone}: {code}")

        return jsonify({'success': True, 'message': f'Код отправлен (тест: {code})'})


    @app.route('/api/auth/verify-otp', methods=['POST'])
    def verify_otp():
        """Проверить OTP-код и войти."""
        data  = request.get_json()
        phone = data.get('phone', '').strip()
        code  = data.get('code', '').strip()
        role  = data.get('role', 'student')

        if not phone.startswith('+998'):
            phone = '+998' + phone

        db = get_db()

        # Проверяем код
        row = db.execute(
            "SELECT * FROM sms_codes WHERE phone=? AND code=? AND used=0 ORDER BY id DESC LIMIT 1",
            (phone, code)
        ).fetchone()

        if not row:
            db.close()
            return jsonify({'error': 'Неверный или истёкший код'}), 400

        # Проверяем время
        expires = datetime.strptime(row['expires_at'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expires:
            db.close()
            return jsonify({'error': 'Код истёк. Запросите новый'}), 400

        # Помечаем код как использованный
        db.execute("UPDATE sms_codes SET used=1 WHERE id=?", (row['id'],))

        # Создаём или получаем пользователя
        user = db.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
        if not user:
            db.execute(
                "INSERT INTO users (phone, role) VALUES (?, ?)",
                (phone, role)
            )
            db.commit()
            user = db.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
        
        db.commit()
        db.close()

        # Сохраняем в сессию
        session['user_id'] = user['id']
        session['role']    = user['role']

        return jsonify({
            'success': True,
            'user': {
                'id':        user['id'],
                'phone':     user['phone'],
                'full_name': user['full_name'],
                'role':      user['role'],
                'score':     user['score'],
                'group':     user['group_name'],
            }
        })


    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        session.clear()
        return jsonify({'success': True})


    @app.route('/api/auth/me', methods=['GET'])
    def me():
        """Получить текущего пользователя."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        db   = get_db()
        user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        db.close()

        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        return jsonify({
            'id':        user['id'],
            'phone':     user['phone'],
            'full_name': user['full_name'],
            'role':      user['role'],
            'score':     user['score'],
            'streak':    user['streak'],
            'level':     user['level'],
            'group':     user['group_name'],
        })

    # ══════════════════════════════════
    #   КУРСЫ
    # ══════════════════════════════════

    @app.route('/api/courses', methods=['GET'])
    def get_courses():
        """Список всех курсов."""
        section = request.args.get('section', '')
        db      = get_db()

        if section:
            rows = db.execute(
                "SELECT * FROM courses WHERE section=?", (section,)
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM courses").fetchall()

        db.close()
        return jsonify([dict(r) for r in rows])


    @app.route('/api/courses/<int:course_id>', methods=['GET'])
    def get_course(course_id):
        """Один курс с модулями."""
        db      = get_db()
        course  = db.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
        if not course:
            db.close()
            return jsonify({'error': 'Курс не найден'}), 404

        modules = db.execute(
            "SELECT * FROM modules WHERE course_id=? ORDER BY order_num",
            (course_id,)
        ).fetchall()

        teacher = None
        if course['teacher_id']:
            t = db.execute("SELECT * FROM users WHERE id=?", (course['teacher_id'],)).fetchone()
            if t:
                teacher = {'name': t['full_name'], 'role': t['group_name']}

        db.close()
        return jsonify({
            **dict(course),
            'modules': [dict(m) for m in modules],
            'teacher': teacher
        })


    @app.route('/api/courses/<int:course_id>/enroll', methods=['POST'])
    def enroll_course(course_id):
        """Записаться на курс."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        db = get_db()
        try:
            db.execute(
                "INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)",
                (user_id, course_id)
            )
            db.commit()
        except Exception:
            pass  # уже записан
        db.close()

        return jsonify({'success': True, 'message': 'Вы записаны на курс!'})

    # ══════════════════════════════════
    #   ПРОГРЕСС И ТЕСТЫ
    # ══════════════════════════════════

    @app.route('/api/progress', methods=['GET'])
    def get_progress():
        """Прогресс студента по всем курсам."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        db   = get_db()
        rows = db.execute('''
            SELECT c.id, c.title, c.emoji,
                   COUNT(m.id)                               AS total_modules,
                   COUNT(p.id)                               AS done_modules
            FROM enrollments e
            JOIN courses c  ON c.id = e.course_id
            LEFT JOIN modules m ON m.course_id = c.id
            LEFT JOIN progress p ON p.module_id = m.id AND p.student_id = e.student_id AND p.done = 1
            WHERE e.student_id = ?
            GROUP BY c.id
        ''', (user_id,)).fetchall()
        db.close()

        result = []
        for r in rows:
            total = r['total_modules'] or 1
            pct   = round(r['done_modules'] / total * 100)
            result.append({
                'course_id':    r['id'],
                'title':        r['title'],
                'emoji':        r['emoji'],
                'done_modules': r['done_modules'],
                'total_modules':total,
                'percent':      pct,
            })
        return jsonify(result)


    @app.route('/api/progress/complete-module', methods=['POST'])
    def complete_module():
        """Отметить модуль как пройденный."""
        user_id   = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        data      = request.get_json()
        module_id = data.get('module_id')
        course_id = data.get('course_id')

        db = get_db()
        existing = db.execute(
            "SELECT id FROM progress WHERE student_id=? AND module_id=?",
            (user_id, module_id)
        ).fetchone()

        if not existing:
            db.execute(
                "INSERT INTO progress (student_id, course_id, module_id, done) VALUES (?,?,?,1)",
                (user_id, course_id, module_id)
            )
            # Добавляем баллы
            db.execute("UPDATE users SET score = score + 20 WHERE id=?", (user_id,))
            db.commit()

        db.close()
        return jsonify({'success': True})


    @app.route('/api/tests/submit', methods=['POST'])
    def submit_test():
        """Сохранить результат теста."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        data      = request.get_json()
        module_id = data.get('module_id')
        score     = data.get('score', 0)
        max_score = data.get('max_score', 20)

        db = get_db()
        db.execute(
            "INSERT INTO test_results (student_id, module_id, score, max_score, completed) VALUES (?,?,?,?,1)",
            (user_id, module_id, score, max_score)
        )
        # Баллы за тест
        db.execute("UPDATE users SET score = score + ? WHERE id=?", (score, user_id))
        db.commit()
        db.close()

        return jsonify({'success': True, 'score': score, 'max_score': max_score})

    # ══════════════════════════════════
    #   СТУДЕНТ — КАБИНЕТ
    # ══════════════════════════════════

    @app.route('/api/student/dashboard', methods=['GET'])
    def student_dashboard():
        """Данные для дашборда студента."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        db   = get_db()
        user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

        # Активные курсы
        courses_count = db.execute(
            "SELECT COUNT(*) FROM enrollments WHERE student_id=?", (user_id,)
        ).fetchone()[0]

        # Пройдено модулей
        modules_done = db.execute(
            "SELECT COUNT(*) FROM progress WHERE student_id=? AND done=1", (user_id,)
        ).fetchone()[0]

        # Долги (незакрытые тесты)
        debts = db.execute('''
            SELECT COUNT(*) FROM modules m
            JOIN enrollments e ON e.course_id = m.course_id AND e.student_id = ?
            LEFT JOIN test_results t ON t.module_id = m.id AND t.student_id = ?
            WHERE t.id IS NULL
        ''', (user_id, user_id)).fetchone()[0]

        # Бейджи
        badges = db.execute(
            "SELECT * FROM badges WHERE student_id=?", (user_id,)
        ).fetchall()

        # Уведомления
        notifs = db.execute(
            "SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 5",
            (user_id,)
        ).fetchall()

        db.close()
        return jsonify({
            'user':          dict(user),
            'courses_count': courses_count,
            'modules_done':  modules_done,
            'debts':         debts,
            'badges':        [dict(b) for b in badges],
            'notifications': [dict(n) for n in notifs],
        })


    @app.route('/api/student/leaderboard', methods=['GET'])
    def leaderboard():
        """Рейтинг группы."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        db   = get_db()
        user = db.execute("SELECT group_name FROM users WHERE id=?", (user_id,)).fetchone()
        group = user['group_name'] if user else ''

        rows = db.execute(
            "SELECT id, full_name, score, level FROM users WHERE role='student' AND group_name=? ORDER BY score DESC LIMIT 20",
            (group,)
        ).fetchall()
        db.close()

        result = []
        for i, r in enumerate(rows):
            result.append({
                'rank':      i + 1,
                'user_id':   r['id'],
                'name':      r['full_name'],
                'score':     r['score'],
                'level':     r['level'],
                'is_me':     r['id'] == user_id,
            })
        return jsonify(result)

    # ══════════════════════════════════
    #   ПРЕПОДАВАТЕЛЬ — КАБИНЕТ
    # ══════════════════════════════════

    @app.route('/api/teacher/group', methods=['GET'])
    def teacher_group():
        """Список студентов группы."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        db      = get_db()
        teacher = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        group   = request.args.get('group', '1001-23 КИ')

        students = db.execute(
            "SELECT id, full_name, score, streak FROM users WHERE role='student' AND group_name=? ORDER BY score DESC",
            (group,)
        ).fetchall()

        result = []
        for s in students:
            done = db.execute(
                "SELECT COUNT(*) FROM test_results WHERE student_id=? AND completed=1", (s['id'],)
            ).fetchone()[0]
            result.append({**dict(s), 'tests_done': done})

        db.close()
        return jsonify({'group': group, 'students': result})


    @app.route('/api/teacher/answers', methods=['GET'])
    def teacher_answers():
        """Открытые ответы для проверки."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        db   = get_db()
        rows = db.execute('''
            SELECT oa.*, u.full_name, m.title AS module_title
            FROM open_answers oa
            JOIN users u   ON u.id = oa.student_id
            JOIN modules m ON m.id = oa.module_id
            WHERE oa.checked = 0
            ORDER BY oa.created_at DESC
        ''').fetchall()
        db.close()

        return jsonify([dict(r) for r in rows])


    @app.route('/api/teacher/answers/<int:answer_id>/grade', methods=['POST'])
    def grade_answer(answer_id):
        """Выставить оценку за открытый ответ."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        data    = request.get_json()
        score   = data.get('score', 0)
        comment = data.get('comment', '')

        db = get_db()
        answer = db.execute("SELECT * FROM open_answers WHERE id=?", (answer_id,)).fetchone()
        if answer:
            db.execute(
                "UPDATE open_answers SET score=?, comment=?, checked=1 WHERE id=?",
                (score, comment, answer_id)
            )
            # Начисляем баллы студенту
            db.execute(
                "UPDATE users SET score = score + ? WHERE id=?",
                (score, answer['student_id'])
            )
            # Уведомление студенту
            db.execute(
                "INSERT INTO notifications (user_id, text, type) VALUES (?,?,?)",
                (answer['student_id'], f'Ваш ответ проверен — {score} баллов', 'success')
            )
            db.commit()
        db.close()

        return jsonify({'success': True})

    # ══════════════════════════════════
    #   ФОРУМ
    # ══════════════════════════════════

    @app.route('/api/forum', methods=['GET'])
    def get_forum():
        """Список тем форума."""
        db   = get_db()
        rows = db.execute('''
            SELECT ft.*, u.full_name,
                   COUNT(fr.id) AS replies_count
            FROM forum_threads ft
            JOIN users u ON u.id = ft.user_id
            LEFT JOIN forum_replies fr ON fr.thread_id = ft.id
            GROUP BY ft.id
            ORDER BY ft.created_at DESC
        ''').fetchall()
        db.close()
        return jsonify([dict(r) for r in rows])


    @app.route('/api/forum', methods=['POST'])
    def create_thread():
        """Создать новую тему."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        data     = request.get_json()
        title    = data.get('title', '').strip()
        body     = data.get('body', '').strip()
        category = data.get('category', 'question')

        if not title:
            return jsonify({'error': 'Заголовок обязателен'}), 400

        db = get_db()
        db.execute(
            "INSERT INTO forum_threads (user_id, title, body, category) VALUES (?,?,?,?)",
            (user_id, title, body, category)
        )
        db.commit()
        db.close()
        return jsonify({'success': True})


    @app.route('/api/forum/<int:thread_id>/reply', methods=['POST'])
    def reply_thread(thread_id):
        """Ответить на тему."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        data = request.get_json()
        body = data.get('body', '').strip()
        if not body:
            return jsonify({'error': 'Ответ не может быть пустым'}), 400

        db = get_db()
        db.execute(
            "INSERT INTO forum_replies (thread_id, user_id, body) VALUES (?,?,?)",
            (thread_id, user_id, body)
        )
        # +5 баллов за ответ на форуме
        db.execute("UPDATE users SET score = score + 5 WHERE id=?", (user_id,))
        db.commit()
        db.close()
        return jsonify({'success': True})

    # ══════════════════════════════════
    #   РАСПИСАНИЕ
    # ══════════════════════════════════

    @app.route('/api/webinars', methods=['GET'])
    def get_webinars():
        """Список вебинаров."""
        section = request.args.get('section', '')
        db      = get_db()

        if section and section != 'all':
            rows = db.execute(
                "SELECT * FROM webinars WHERE section=? ORDER BY date_time", (section,)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM webinars ORDER BY date_time"
            ).fetchall()

        db.close()
        return jsonify([dict(r) for r in rows])

    # ══════════════════════════════════
    #   ДНЕВНИК ОБУЧЕНИЯ
    # ══════════════════════════════════

    @app.route('/api/diary', methods=['GET'])
    def get_diary():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        db   = get_db()
        rows = db.execute(
            "SELECT * FROM diary WHERE student_id=? ORDER BY id DESC",
            (user_id,)
        ).fetchall()
        db.close()
        return jsonify([dict(r) for r in rows])


    @app.route('/api/diary', methods=['POST'])
    def add_diary():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401

        data      = request.get_json()
        text      = data.get('text', '').strip()
        course_id = data.get('course_id')

        if not text:
            return jsonify({'error': 'Текст записи пуст'}), 400

        db = get_db()
        db.execute(
            "INSERT INTO diary (student_id, course_id, text) VALUES (?,?,?)",
            (user_id, course_id, text)
        )
        db.commit()
        db.close()
        return jsonify({'success': True})

    # ══════════════════════════════════
    #   ИНИЦИАЛИЗАЦИЯ ДАННЫХ
    # ══════════════════════════════════

    @app.route('/api/seed', methods=['POST'])
    def seed():
        """Заполнить БД тестовыми данными (только для разработки)."""
        seed_db()
        return jsonify({'success': True, 'message': 'Тестовые данные добавлены'})

    # ══════════════════════════════════
    #   HEALTH CHECK
    # ══════════════════════════════════

    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'app': 'ЭдуПлатформа', 'version': '1.0'})
