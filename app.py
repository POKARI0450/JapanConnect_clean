import os
import time
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
# 修正後
from urllib.parse import quote as url_quote

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.root_path, 'japanconnect.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SEND_FILE_MAX_AGE_DEFAULT=0,
    TEMPLATES_AUTO_RELOAD=True
)
db = SQLAlchemy(app)

def get_file_mtime(filepath):
    try:
        return int(os.path.getmtime(filepath))
    except OSError:
        return int(time.time())

@app.context_processor
def inject_vars():
    return {
        'cache_bust': time.time(),
        'static_css': lambda: url_for('static', filename='css/style.css') + f'?v={get_file_mtime("static/css/style.css")}'
    }

# グローバルなデモ用ヘルパーデータ
helpers_data = [
    {
        "id": 1,
        "username": "山田 太郎",
        "photo": "helper1.jpg",
        "intro": "東京都在住。長年の経験をもとに、旅行者のサポートを行っています。",
        "rating": 5.0,
        "languages": ["日本語", "英語"],
        "scores": {"TOEIC": 900, "IELTS": 7.5},
        "region": "東京、神奈川",
        "experience": "5年（累計100件のサポート実績）",
        "is_newcomer": False
    },
    {
        "id": 2,
        "username": "佐藤 花子",
        "photo": "helper_new.jpg",
        "intro": "新人ながらも情熱を持ってお手伝いします！",
        "rating": 4.5,
        "languages": ["英語", "中国語"],
        "scores": {"TOEIC": 850, "IELTS": 7.0},
        "region": "横浜、川崎",
        "experience": "1年（少数ですが確かな実績）",
        "is_newcomer": True
    },
    {
        "id": 3,
        "username": "ジョン・スミス",
        "photo": "helper3.jpg",
        "intro": "海外出身ですが、日本での生活にも慣れており、親切にお手伝いします。",
        "rating": 4.2,
        "languages": ["英語"],
        "scores": {"TOEFL": 95},
        "region": "東京全域",
        "experience": "4年（多数のサポート実績）",
        "is_newcomer": False
    }
]

# トップページ（フォーム表示）
@app.route('/')
def index():
    return render_template('index.html')

# フォーム送信後のルート（POSTのみ受け付ける）
@app.route('/create_request', methods=['POST', 'GET'])
def create_request():
    if request.method == 'GET':
        return redirect(url_for('index'))
    
    category = request.form.get('category')
    location = request.form.get('location')
    language = request.form.get('language')
    
    # シンプルに全データを評価順（新人優先）に並べ替える
    sorted_helpers = sorted(helpers_data, key=lambda h: (not h["is_newcomer"], -h["rating"]))
    
    return render_template('results_new.html', helpers=sorted_helpers, category=category, location=location)

# 詳細プロフィールページのルート
@app.route('/profile/<int:helper_id>')
def profile(helper_id):
    helper = next((h for h in helpers_data if h["id"] == helper_id), None)
    if not helper:
        return "ヘルパーが見つかりませんでした。", 404
    return render_template('profile.html', helper=helper)

if __name__ == "__main__":
    app.run(debug=True, port=5007)
