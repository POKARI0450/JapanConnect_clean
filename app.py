import os
import time
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # セッション用の秘密鍵
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///japanconnect.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SEND_FILE_MAX_AGE_DEFAULT=0,  # 静的ファイルのキャッシュを無効化
    TEMPLATES_AUTO_RELOAD=True,
    UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB制限
)

# データベースの初期化
db = SQLAlchemy(app)

# Flask-Loginの設定
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ユーザーモデル
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_helper = db.Column(db.Boolean, default=True)  # True: ヘルパー（旅行者向け）, False: ガイド
    help_count = db.Column(db.Integer, default=0)
    rating_sum = db.Column(db.Integer, default=0)
    rating_count = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)

    @property
    def rating(self):
        if self.rating_count == 0:
            return 0
        return self.rating_sum / self.rating_count

    def __repr__(self):
        return f'<User {self.username}>'

# プロフィールモデル（1:1関係）
class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    photo = db.Column(db.String(200), default="default.jpg")
    intro = db.Column(db.Text, default="自己紹介が設定されていません。")
    languages = db.Column(db.String(200), default="日本語")
    region = db.Column(db.String(100), default="不明")
    experience = db.Column(db.String(100), default="未経験")
    # 絞り込み用のカテゴリー情報（カンマ区切り）
    help_categories = db.Column(db.String(200), default="")
    user = db.relationship('User', backref=db.backref('profile', uselist=False))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 静的ファイルのキャッシュバスティング用関数
@app.context_processor
def inject_vars():
    def get_file_mtime(filepath):
        try:
            return int(os.path.getmtime(filepath))
        except OSError:
            return int(time.time())
    return {
        'cache_bust': time.time(),
        'static_css': lambda: url_for('static', filename='css/style.css') + f'?v={get_file_mtime("static/css/style.css")}'
    }

# datetime モジュールをテンプレートで利用できるようにする
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# ルート定義

# ホーム：ヘルパー一覧（base.html を継承する index.html）
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

# 検索ページのルート
@app.route('/search', methods=['GET', 'POST'])
def search():
    # すべてのヘルパーを取得
    helpers = User.query.filter_by(is_helper=True).all()
    
    # 検索結果ページを直接表示
    return render_template('search_results.html', helpers=helpers)

# ヘルプリクエストページ
@app.route('/help_request')
def help_request():
    return render_template('search.html')

# 検索結果ページを直接表示するルート
@app.route('/search_results')
def search_results():
    helpers = User.query.filter_by(is_helper=True).all()
    return render_template('search_results.html', helpers=helpers)

# 料金プランページ：/pricing
@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# create_request: ホームのリクエストフォーム送信用 /create_request
@app.route('/create_request', methods=['POST'])
def create_request():
    category = request.form.get('category')
    location = request.form.get('location')
    language = request.form.get('language')
    helpers = User.query.join(Profile).filter(
        User.is_helper == True,
        Profile.help_categories.contains(category),
        Profile.region.contains(location),
        Profile.languages.contains(language)
    ).all()
    flash("リクエストが送信されました。", "success")
    return render_template('search_results.html', helpers=helpers, category=category, location=location, language=language)

# ログイン：/login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        # ユーザーが存在し、パスワードが正しい場合
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            return redirect(url_for('index'))
        
        # ログイン失敗
        flash('メールアドレスまたはパスワードが正しくありません。')
        return redirect(url_for('login'))
    
    # GETリクエストの場合、ログインページを表示
    return render_template('login.html')

# ログアウト：/logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("ログアウトしました。", "info")
    return redirect(url_for('index'))

# 旅行者登録：/traveler_signup
@app.route('/traveler_signup', methods=['GET', 'POST'])
def traveler_signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("ユーザー名またはメールアドレスは既に存在します。", "danger")
            return redirect(url_for('traveler_signup'))
        new_user = User(username=username, email=email,
                        password_hash=generate_password_hash(password),
                        is_helper=True)
        db.session.add(new_user)
        db.session.commit()
        new_profile = Profile(user_id=new_user.id)
        db.session.add(new_profile)
        db.session.commit()
        flash("旅行者として登録が完了しました。", "success")
        return redirect(url_for('login'))
    return render_template('traveler_signup.html')

# ガイド登録：/guide_signup
@app.route('/guide_signup', methods=['GET', 'POST'])
def guide_signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        region = request.form.get('region')
        language = request.form.get('language')
        intro = request.form.get('intro')
        support_types = request.form.getlist('support_types')
        skills = request.form.get('skills')
        
        # ユーザーが既に存在するか確認
        user = User.query.filter_by(email=email).first()
        if user:
            flash('このメールアドレスは既に登録されています。')
            return redirect(url_for('guide_signup'))
        
        # 新しいユーザーを作成
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_helper=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # プロフィールを作成
        new_profile = Profile(
            user_id=new_user.id,
            region=region,
            languages=language,
            intro=intro,
            skills=skills,
            support_types=','.join(support_types) if support_types else ''
        )
        
        db.session.add(new_profile)
        db.session.commit()
        
        # 自動ログイン
        login_user(new_user)
        
        flash('ガイドとして登録が完了しました！')
        return redirect(url_for('index'))
    
    return render_template('guide_signup.html')

# 評価機能：/rate/<helper_id>
@app.route('/rate/<int:helper_id>', methods=['POST'])
def rate_helper(helper_id):
    if not current_user.is_authenticated:
        flash("評価するにはログインが必要です。", "warning")
        return redirect(url_for('login'))
    helper = User.query.get(helper_id)
    if not helper:
        flash("ヘルパーが見つかりません。", "danger")
        return redirect(url_for('index'))
    try:
        rating = int(request.form.get('rating', 0))
    except (TypeError, ValueError):
        rating = 0
    if rating < 1 or rating > 5:
        flash("評価は1〜5の間で入力してください。", "danger")
        return redirect(url_for('profile', helper_id=helper_id))
    helper.rating_sum += rating
    helper.rating_count += 1
    db.session.commit()
    flash("評価が送信されました！", "success")
    return redirect(url_for('profile', helper_id=helper_id))

# いいね機能：/like/<helper_id>
@app.route('/like/<int:helper_id>', methods=['POST'])
def like(helper_id):
    if not current_user.is_authenticated:
        return jsonify({'error': 'ログインが必要です'}), 401
    helper = User.query.get(helper_id)
    if not helper:
        return jsonify({'error': 'ヘルパーが見つかりません'}), 404
    helper.likes = (helper.likes or 0) + 1
    db.session.commit()
    return jsonify({'likes': helper.likes})

# ブックマーク機能：/bookmark/<helper_id>
@app.route('/bookmark/<int:helper_id>', methods=['POST'])
def bookmark(helper_id):
    if not current_user.is_authenticated:
        return jsonify({'error': 'ログインが必要です'}), 401
    bookmarks = session.get('bookmarks', [])
    if helper_id not in bookmarks:
        bookmarks.append(helper_id)
        session['bookmarks'] = bookmarks
    return jsonify({'bookmarks': len(bookmarks)})

# コンタクト機能：/contact/<helper_id>
@app.route('/contact/<int:helper_id>', methods=['GET', 'POST'])
def contact(helper_id):
    helper = User.query.get(helper_id)
    if not helper:
        flash("ヘルパーが見つかりません。", "danger")
        return redirect(url_for('index'))
    if request.method == 'POST':
        message = request.form.get('message')
        # 問い合わせ内容の保存やメール送信処理など実装（省略）
        flash("メッセージが送信されました！", "success")
        return redirect(url_for('profile', helper_id=helper_id))
    return render_template('contact.html', helper=helper)

# プロフィール詳細ページ：/profile/<helper_id>
@app.route('/profile/<int:helper_id>', methods=['GET', 'POST'])
def profile(helper_id):
    helper = User.query.get(helper_id)
    if not helper or not helper.profile:
        return "ヘルパーが見つかりませんでした。", 404
    if request.method == 'POST':
        try:
            rating = int(request.form.get('rating'))
        except (TypeError, ValueError):
            rating = 0
        helper.rating_sum += rating
        helper.rating_count += 1
        db.session.commit()
        flash("評価が更新されました。", "success")
        return redirect(url_for('profile', helper_id=helper_id))
    return render_template('profile.html', helper=helper)

# お問い合わせフォーム処理用のルートを追加
@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # ここで実際にはメール送信などの処理を行いますが、
        # このサンプルではデータを受け取るだけにします
        
        # フラッシュメッセージを設定
        flash('お問い合わせありがとうございます。担当者からご連絡いたします。', 'success')
        
        # お問い合わせ完了ページにリダイレクト
        return render_template('contact_complete.html', name=name, email=email)
    
    # POSTメソッド以外の場合はトップページにリダイレクト
    return redirect(url_for('index'))

# お問い合わせページ表示用のルート
@app.route('/contact_page')
def contact_page():
    return render_template('contact.html')

@app.route('/service-details')
def service_details():
    return render_template('service_details.html')

def create_demo_data():
    try:
        # 既存のテーブルを削除して再作成
        db.drop_all()
        db.create_all()
        print("データベーステーブルを再作成しました。")
        
        # デモユーザーを作成
        demo_user = User(
            username="田中太郎",
            email="demo@example.com",
            password_hash=generate_password_hash("password"),
            is_helper=True,
            help_count=5,
            rating_sum=20,
            rating_count=5,
            likes=10
        )
        db.session.add(demo_user)
        
        # 田中太郎のプロフィールを作成
        tanaka_profile = Profile(
            user=demo_user,
            intro="東京在住5年目のガイドです。英語が得意で、日本の文化を紹介するのが好きです。",
            languages="日本語,英語",
            region="東京",
            experience="5年",
            photo="tanaka.jpg"
        )
        db.session.add(tanaka_profile)
        
        # 佐藤花子のユーザーを作成
        sato_hanako = User(
            username="佐藤花子",
            email="hanako@example.com",
            password_hash=generate_password_hash("password"),
            is_helper=True,
            help_count=2,
            rating_sum=8,
            rating_count=2,
            likes=5
        )
        db.session.add(sato_hanako)
        
        # 佐藤花子のプロフィールを作成
        hanako_profile = Profile(
            user=sato_hanako,
            intro="新人ですが情熱を持ってお手伝いします！",
            languages="日本語,英語",
            region="東京",
            experience="1年",
            photo="hanako.jpg"
        )
        db.session.add(hanako_profile)
        
        # 山田健太のユーザーを作成（3人目のヘルパー）
        yamada_kenta = User(
            username="山田健太",
            email="kenta@example.com",
            password_hash=generate_password_hash("password"),
            is_helper=True,
            help_count=8,
            rating_sum=36,
            rating_count=8,
            likes=15
        )
        db.session.add(yamada_kenta)
        
        # 山田健太のプロフィールを作成
        kenta_profile = Profile(
            user=yamada_kenta,
            intro="関西出身のガイドです。大阪の観光スポットに詳しいです。",
            languages="日本語,英語,中国語",
            region="大阪",
            experience="3年",
            photo="kenta.jpg"
        )
        db.session.add(kenta_profile)
        
        # デモガイドを作成
        demo_guide = User(
            username="demo_guide",
            email="guide@example.com",
            password_hash=generate_password_hash("password"),
            is_helper=False,
            help_count=10,
            rating_sum=45,
            rating_count=10
        )
        db.session.add(demo_guide)
        
        # ガイドのプロフィールを作成
        guide_profile = Profile(
            user=demo_guide,
            intro="日本の文化と歴史に詳しいガイドです。",
            languages="日本語,英語,中国語",
            region="東京",
            experience="5年",
            photo="guide1.jpg"
        )
        db.session.add(guide_profile)
        
        db.session.commit()
        print("デモデータを作成しました。")
    except Exception as e:
        print(f"デモデータ作成中にエラーが発生しました: {e}")
        db.session.rollback()

if __name__ == '__main__':
    import os
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5002)))
