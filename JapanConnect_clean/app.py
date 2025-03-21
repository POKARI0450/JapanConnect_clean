from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# データベースモデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'traveler' or 'guide'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ガイド用の追加情報
    languages = db.Column(db.String(200))
    location = db.Column(db.String(100))
    bio = db.Column(db.Text)
    rating = db.Column(db.Float, default=0.0)
    reviews_count = db.Column(db.Integer, default=0)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ルート
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/helpers')
def helpers():
    # 実際のアプリケーションでは、データベースからガイド情報を取得します
    guides = [
        {
            'name': '山田 太郎',
            'languages': '日本語, 英語, 中国語',
            'location': '東京',
            'bio': '東京在住のガイドです。英語と中国語が話せます。東京の観光スポットや隠れた名所をご案内します。',
            'rating': 4.9,
            'reviews_count': 28
        },
        {
            'name': '佐藤 花子',
            'languages': '日本語, 英語, フランス語',
            'location': '京都',
            'bio': '京都在住のガイドです。英語とフランス語が話せます。伝統的な京都の文化体験をご案内します。',
            'rating': 5.0,
            'reviews_count': 42
        },
        {
            'name': '鈴木 一郎',
            'languages': '日本語, 英語, スペイン語',
            'location': '大阪',
            'bio': '大阪在住のガイドです。英語とスペイン語が話せます。大阪のグルメツアーが得意です！',
            'rating': 4.0,
            'reviews_count': 35
        }
    ]
    return render_template('helpers.html', guides=guides)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # データベースにメッセージを保存
        new_message = ContactMessage(name=name, email=email, subject=subject, message=message)
        db.session.add(new_message)
        db.session.commit()
        
        # フラッシュメッセージを表示（実際のアプリケーションでは）
        # flash('メッセージが送信されました。ありがとうございます！', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    user_type = request.args.get('type', 'traveler')
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        # ガイド用の追加情報
        languages = None
        location = None
        bio = None
        
        if user_type == 'guide':
            languages = ','.join(request.form.getlist('languages'))
            location = request.form.get('location')
            bio = request.form.get('bio')
        
        # データベースにユーザーを保存
        new_user = User(
            name=name, 
            email=email, 
            password=password,  # 実際のアプリケーションではハッシュ化する
            user_type=user_type,
            languages=languages,
            location=location,
            bio=bio
        )
        db.session.add(new_user)
        db.session.commit()
        
        # フラッシュメッセージを表示（実際のアプリケーションでは）
        # flash('アカウントが作成されました。ログインしてください。', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html', user_type=user_type)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 実際のアプリケーションでは、データベースからユーザーを検索し、
        # パスワードを検証します
        
        # フラッシュメッセージを表示（実際のアプリケーションでは）
        # flash('ログインしました。', 'success')
        return redirect(url_for('index'))
    
    return render_template('login.html')

# データベース初期化
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
