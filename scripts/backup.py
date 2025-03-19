import os
import shutil
import datetime
import sys

def backup_project(src_dir, backup_dir):
    # バックアップ先ディレクトリが存在しない場合は作成
    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir)
            print(f"Created backup directory: {backup_dir}")
        except Exception as e:
            print(f"Error creating backup directory: {e}")
            return False
    
    # タイムスタンプ付きのバックアップディレクトリ名を作成
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = os.path.join(backup_dir, f"backup_{now}")
    
    try:
        # バックアップを実行
        print(f"Starting backup from {src_dir} to {dest_dir}...")
        shutil.copytree(src_dir, dest_dir, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo', '.git'))
        print(f"Backup successfully created at {dest_dir}")
        return True
    except Exception as e:
        print(f"Error during backup: {e}")
        return False

if __name__ == "__main__":
    # プロジェクトのルートディレクトリを取得
    # スクリプトが scripts/ フォルダにある場合、一階層上がプロジェクトルート
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # バックアップ先ディレクトリを指定
    # ユーザーのホームディレクトリ内に JapanConnect_backups フォルダを作成
    home_dir = os.path.expanduser("~")
    backup_dir = os.path.join(home_dir, "JapanConnect_backups")
    
    print(f"Project root: {project_root}")
    print(f"Backup directory: {backup_dir}")
    
    # バックアップを実行
    success = backup_project(project_root, backup_dir)
    
    if success:
        print("Backup completed successfully.")
        sys.exit(0)
    else:
        print("Backup failed.")
        sys.exit(1)

# プロジェクトディレクトリをパスに追加
path = '/home/pokamoto/japanconnect_1'  # GitHubからクローンした場合
# または
# path = '/home/pokamoto/mysite'  # 既存のディレクトリを使用する場合

if path not in sys.path:
    sys.path.append(path)

# Flaskアプリケーションをインポート
from app import app as application
