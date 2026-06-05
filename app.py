from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from models import init_db
from routes import register_routes
import os

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, supports_credentials=True)

# Все файлы лежат в одной папке с app.py
FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    if filename.startswith('api/'):
        return "Not found", 404
    try:
        return send_from_directory(FRONTEND_DIR, filename)
    except:
        return send_from_directory(FRONTEND_DIR, 'index.html')

# Инициализация БД
init_db()

# Регистрация маршрутов
register_routes(app)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("=" * 50)
    print("  ЭдуПлатформа — Flask сервер запущен!")
    print(f"  http://0.0.0.0:{port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)