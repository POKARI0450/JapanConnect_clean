from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # セッション用の秘密鍵

# 画像アップロード用の設定
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB制限

app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def index():
    helpers = [
        {
            'username': '山田 太郎',
            'profile': {
                'intro': '東京在住10年のガイドです。英語と中国語が話せます。東京の隠れた名所をご案内します！',
                'languages': '日本語, 英語, 中国語',
                'region': '東京',
                'photo': 'helper1.jpg'
            },
            'rating': 4.5,
            'rating_count': 28
        },
        {
            'username': '佐藤 花子',
            'profile': {
                'intro': '京都在住のガイドです。英語とフランス語が話せます。伝統的な京都の文化体験をご案内します。',
                'languages': '日本語, 英語, フランス語',
                'region': '京都',
                'photo': 'helper2.jpg'
            },
            'rating': 5.0,
            'rating_count': 42
        },
        {
            'username': '鈴木 一郎',
            'profile': {
                'intro': '大阪在住のガイドです。英語とスペイン語が話せます。大阪のグルメツアーが得意です！',
                'languages': '日本語, 英語, スペイン語',
                'region': '大阪',
                'photo': 'helper3.jpg'
            },
            'rating': 4.0,
            'rating_count': 35
        }
    ]
    return render_template('index.html', helpers=helpers)

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/search_results')
def search_results():
    return render_template('search_results.html')

@app.route('/helpers')
def helpers():
    return render_template('helpers.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/register')
def register():
    user_type = request.args.get('type', 'traveler')
    return render_template('register.html', user_type=user_type)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
