from flask import Flask, render_template, redirect, url_for, flash, request, session
import os
from supabase import create_client
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# .envファイルから環境変数を読み込む
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')

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

# ユーザークラスの定義
class User(UserMixin):
    def __init__(self, id, email, name=None):
        self.id = id
        self.email = email
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    # Supabaseからユーザー情報を取得
    response = supabase.table('users').select('*').eq('id', user_id).execute()
    if response.data:
        user_data = response.data[0]
        return User(user_data['id'], user_data['email'], user_data.get('name'))
    return None

@app.route('/')
def home():
    return render_template('index.html')  # 'Hello, World!'の代わりにindex.htmlを表示

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Supabaseで認証
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            user = User(response.user.id, response.user.email)
            login_user(user)
            flash('ログインしました', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash('ログインに失敗しました', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Supabaseで登録
        try:
            response = supabase.auth.sign_up({"email": email, "password": password})
            flash('登録が完了しました。ログインしてください。', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('登録に失敗しました', 'danger')
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('ログアウトしました', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
# Updated on Fri Mar 21 23:22:05 JST 2025
