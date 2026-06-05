import os

class Config:
    SECRET_KEY = 'edu-platform-secret-key-2024'
    DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'db.sqlite3')
    DEBUG       = True

    # Eskiz.uz SMS (замени на свои данные)
    ESKIZ_EMAIL   = 'your@email.com'
    ESKIZ_PASSWORD = 'your_password'

    # Для теста — фиксированный OTP-код (убери в продакшне)
    TEST_OTP = '1234'
