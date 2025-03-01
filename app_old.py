import os
import time
from datetime import datetime
from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.root_path, 'japanconnect.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SEND_FILE_MAX_AGE_DEFAULT=0,
    TEMPLATES_AUTO_RELOAD=True
)
db = SQLAlchemy(app)

# app オブジェクト定義後に get_file_mtime を定義
def get_file_mtime(path):
    return int(os.path.getmtime(os.path.join(app.root_path, path)))

# コンテキストプロセッサで静的ファイルのキャッシュバスティング関数を注入
@app.context_processor
def inject_vars():
    return {
        'cache_bust': time.time(),
        'static_css': lambda: url_for('static', filename='css/style.css') + f'?v={get_file_mtime("static/css/style.css")}'
    }

# その後、他のコード（DBモデル、ルート定義など）
# 例：
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    languages = db.Column(db.String(200), nullable=False)
    availability = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Float, default=4.5)
    created_at = db.Column(db.DateTime, default=datetime.now)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5006)
@app.route('/create_request', methods=['POST'])
def create_request():
    # フォームからデータを取得する例
    category = request.form['category']
    location = request.form['location']
    language = request.form['language']

    # ※ 本来はここでヘルパー検索の処理を実施
    # 仮のヘルパーデータ（実際はDBから取得するなど）
    helpers = [
        {"username": "山田 太郎", "languages": "日本語・英語", "rating": 5.0, "is_newcomer": False},
        {"username": "佐藤 花子", "languages": "英語・中国語", "rating": 4.5, "is_newcomer": True},
        {"username": "ジョン・スミス", "languages": "英語", "rating": 4.2, "is_newcomer": False},
    ]

    # 例えば、新人を上位にして評価順に並べる処理
    sorted_helpers = sorted(helpers, key=lambda h: (not h["is_newcomer"], -h["rating"]))

    return render_template('results.html', helpers=sorted_helpers, category=category, location=location, language=language)
