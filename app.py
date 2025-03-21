from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# .envファイルから環境変数を読み込む
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')

# SQLAlchemyの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # メモリ内SQLiteを使用
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Supabaseの設定 - 明示的にデフォルト値を設定
supabase_url = os.environ.get('SUPABASE_URL', 'https://uwsvmipqroqbqotiyypt.supabase.co')
supabase_key = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV3c3ZtaXBxcm9xYnFvdGl5eXB0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIzNjc4NzksImV4cCI6MjA1Nzk0Mzg3OX0.OurNtxec26ZowY8y6w9latJaFfPW3TPDB_QCBIcFuIg')

# 値が空でないことを確認
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

print(f"Using Supabase URL: {supabase_url}")
supabase = create_client(supabase_url, supabase_key)

# Flask-Loginの設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# データベースモデル
class User(db.Model, UserMixin):
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

@login_manager.user_loader
def load_user(user_id):
    # Supabaseからユーザー情報を取得
    response = supabase.table('users').select('*').eq('id', user_id).execute()
    if response.data:
        user_data = response.data[0]
        return User(user_data['id'], user_data['email'], user_data.get('name'))
    return None

# コンテキストプロセッサ - ユーザー情報をテンプレートに注入
@app.context_processor
def inject_user():
    return {
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'user_type': session.get('user_type')
    }

# ルート: ホームページ
@app.route('/')
def home():
    return render_template('index.html')  # 'Hello, World!'の代わりにindex.htmlを表示

# ルート: ヘルパー一覧
@app.route('/helpers')
def helpers():
    # Supabaseからヘルパー情報を取得
    response = supabase.table('users').select('id, username').eq('user_type', 'helper').execute()
    helpers_data = response.data
    
    # ヘルパープロフィール情報を取得
    helper_profiles = {}
    if helpers_data:
        helper_ids = [helper['id'] for helper in helpers_data]
        profiles_response = supabase.table('helper_profiles').select('*').in_('user_id', helper_ids).execute()
        
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
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        # 入力検証
        if not username or not email or not password or not user_type:
            flash('すべてのフィールドを入力してください')
            return redirect(url_for('register'))
        
        # ユーザー名とメールの重複チェック
        response = supabase.table('users').select('id').or_(f'username.eq.{username},email.eq.{email}').execute()
        if response.data:
            flash('そのユーザー名またはメールアドレスは既に使用されています')
            return redirect(url_for('register'))
        
        # パスワードハッシュ化
        password_hash = generate_password_hash(password)
        
        # 新しいユーザーを作成
        user_id = str(uuid.uuid4())
        user_data = {
            'id': user_id,
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'user_type': user_type
        }
        
        response = supabase.table('users').insert(user_data).execute()
        
        # ヘルパーの場合、プロフィールも作成
        if user_type == 'helper':
            profile_data = {
                'user_id': user_id,
                'bio': '',
                'languages': [],
                'areas': [],
                'skills': [],
                'hourly_rate': 0,
                'is_available': True
            }
            supabase.table('helper_profiles').insert(profile_data).execute()
        
        flash('登録が完了しました。ログインしてください。')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# ルート: ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 入力検証
        if not email or not password:
            flash('メールアドレスとパスワードを入力してください')
            return redirect(url_for('login'))
        
        # ユーザーを検索
        response = supabase.table('users').select('*').eq('email', email).execute()
        
        if not response.data:
            flash('メールアドレスまたはパスワードが正しくありません')
            return redirect(url_for('login'))
        
        user = response.data[0]
        
        # パスワード検証
        if check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            
            flash(f'ようこそ、{user["username"]}さん！')
            return redirect(url_for('index'))
        else:
            flash('メールアドレスまたはパスワードが正しくありません')
            return redirect(url_for('login'))
    
    return render_template('login.html')

# ルート: ログアウト
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('user_type', None)
    flash('ログアウトしました')
    return redirect(url_for('index'))

# ルート: プロフィール
@app.route('/profile')
@login_required
def profile():
    # ユーザー情報を取得
    response = supabase.table('users').select('*').eq('id', session['user_id']).execute()
    user = response.data[0] if response.data else None
    
    # ヘルパープロフィール情報を取得（ヘルパーの場合）
    profile = None
    if user and user['user_type'] == 'helper':
        profile_response = supabase.table('helper_profiles').select('*').eq('user_id', user['id']).execute()
        profile = profile_response.data[0] if profile_response.data else None
    
    return render_template('profile.html', user=user, profile=profile)

# ルート: ダッシュボード（ヘルパー用）
@app.route('/dashboard')
@login_required
def dashboard():
    # ユーザー情報を取得
    response = supabase.table('users').select('*').eq('id', session['user_id']).execute()
    user = response.data[0] if response.data else None
    
    # ヘルパープロフィール情報を取得
    profile_response = supabase.table('helper_profiles').select('*').eq('user_id', user['id']).execute()
    profile = profile_response.data[0] if profile_response.data else None
    
    # メッセージ数を取得
    messages_response = supabase.table('messages').select('count').eq('receiver_id', user['id']).execute()
    message_count = messages_response.count if hasattr(messages_response, 'count') else 0
    
    return render_template('dashboard.html', user=user, profile=profile, message_count=message_count)

# ルート: 料金プラン
@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# ルート: お問い合わせ
@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
