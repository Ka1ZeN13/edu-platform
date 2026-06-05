from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from models import init_db
from routes import register_routes
import os

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, supports_credentials=True)

# Папка с фронтендом (на уровень выше от backend/)
FRONTEND_DIR = os.path.dirname(__file__)

# Раздача HTML страниц
@app.route('/')
@app.route('/<path:filename>')
def serve_frontend(filename='index.html'):
    # Если запрос к API — пропускаем
    if filename.startswith('api/'):
        return "Not found", 404
    return send_from_directory(FRONTEND_DIR, filename)

# Инициализация базы данных
init_db()
 
# Регистрация маршрутов
register_routes(app)

if __name__ == '__main__':
    print("=" * 50)
    print("  ЭдуПлатформа — Flask сервер запущен!")
    print("  http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)