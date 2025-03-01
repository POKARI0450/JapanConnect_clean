from flask import Flask, render_template, request

app = Flask(__name__)

# トップページ（検索フォーム）
@app.route('/')
def index():
    return render_template('index.html')

# 検索処理
@app.route('/search', methods=['POST'])
def search():
    category = request.form['category']
    location = request.form['location']
    language = request.form['language']

    # 仮のデータ（本来はDBやAPIから取得）
    helpers = [
        {"name": "山田 太郎", "rating": 5.0, "languages": "日本語・英語", "image": "helper1.jpg", "newcomer": False},
        {"name": "佐藤 花子", "rating": 4.5, "languages": "英語・中国語", "image": "helper_new.jpg", "newcomer": True},
        {"name": "ジョン・スミス", "rating": 4.2, "languages": "英語", "image": "helper3.jpg", "newcomer": False}
    ]

    # 新人を最上位にし、それ以外は評価順でソート
    sorted_helpers = sorted(helpers, key=lambda x: (-x["newcomer"], -x["rating"]))

    return render_template('results.html', helpers=sorted_helpers)

if __name__ == '__main__':
    app.run(debug=True, port=5006)
