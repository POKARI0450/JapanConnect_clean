from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World! JapanConnect is running with Supabase integration."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
