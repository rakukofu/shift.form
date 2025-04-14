from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_wtf.csrf import CSRFProtect, generate_csrf

# 環境変数と設定
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 5,
    'max_overflow': 10,
    'pool_timeout': 30,
    'connect_args': {
        'sslmode': 'require',
        'connect_timeout': 10
    }
}

# 管理者パスワード
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '0131')

# 初期化
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'
login_manager.login_message = 'ログインが必要です。'
login_manager.login_message_category = 'error'
csrf = CSRFProtect(app)

# モデル
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=False)
    user_name = db.Column(db.String(50), nullable=False)
    morning = db.Column(db.String(50), nullable=True)
    afternoon = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            'date': self.date,
            'user_name': self.user_name,
            'morning': self.morning,
            'afternoon': self.afternoon
        }

# ログインユーザー情報を取得
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# データベースの作成
with app.app_context():
    db.create_all()

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('アクセス権限がありません。管理者としてログインしてください。', 'error')
        return redirect(url_for('admin_login'))  
    try:
        users = User.query.all()
        return render_template('admin.html', users=users)
    except Exception as e:
        app.logger.error(f'管理者ダッシュボードエラー: {str(e)}')
        return render_template('500.html'), 500

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    try:
        if request.method == 'POST':
            password = request.form.get('password')
            csrf_token = request.form.get('csrf_token')
            
            if not csrf_token:
                flash('CSRFトークンがありません。', 'error')
                return redirect(url_for('admin_login'))
                
            if password == ADMIN_PASSWORD:
                session['is_admin'] = True
                session['admin_login_time'] = datetime.now().timestamp()  # ログイン時刻を記録
                flash('管理者としてログインしました。', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('パスワードが間違っています。', 'error')
        return render_template('admin_login.html')
    except Exception as e:
        app.logger.error(f'管理者ログインエラー: {str(e)}')
        return render_template('500.html'), 500

@app.route('/admin/users/add', methods=['GET', 'POST'])
def add_user():
    if not session.get('is_admin'):
        flash('アクセス権限がありません。管理者としてログインしてください。', 'error')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        csrf_token = request.form.get('csrf_token')
        
        if not csrf_token:
            flash('CSRFトークンがありません。', 'error')
            return redirect(url_for('add_user'))
        
        if not username or not password:
            flash('ユーザー名とパスワードは必須です。', 'error')
            return redirect(url_for('add_user'))
        
        # パスワードをハッシュ化
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # 新しいユーザーを作成
        new_user = User(username=username, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('ユーザーを追加しました。', 'success')
        except Exception as e:
            db.session.rollback()
            flash('ユーザーの追加に失敗しました。', 'error')
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_user.html')
    
@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not session.get('is_admin'):
        flash('アクセス権限がありません。管理者としてログインしてください。', 'error')
        return redirect(url_for('admin_login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('指定されたユーザーが見つかりません。', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            flash('CSRFトークンがありません。', 'error')
            return redirect(url_for('edit_user', user_id=user_id))
            
        user.username = request.form['username']
        new_password = request.form['password']
        if new_password:
            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        flash('ユーザー情報を更新しました。', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_user.html', user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('is_admin'):
        flash('アクセス権限がありません。管理者としてログインしてください。', 'error')
        return redirect(url_for('admin_login'))
    
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'ユーザー {user.username} を削除しました。', 'success')
    else:
        flash('指定されたユーザーが見つかりません。', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_logout')
def admin_logout():
    session.pop('is_admin', None)
    session.pop('admin_login_time', None)
    flash('管理者としてログアウトしました。', 'success')
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            # ログイン処理
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                flash('ログインしました。', 'success')
                return redirect(url_for('index'))
            else:
                flash('ユーザー名またはパスワードが間違っています。', 'error')
                return redirect(url_for('index'))
        
        try:
            # CSRFトークンの検証
            csrf_token = request.form.get('csrf_token')
            if not csrf_token:
                return jsonify({'category': 'error', 'message': 'CSRFトークンがありません'}), 403

            # シフトデータの処理
            for key, value in request.form.items():
                if '-' in key and (key.endswith('-morning') or key.endswith('-afternoon')):
                    date_str = key.rsplit('-', 1)[0]
                    shift_type = key.split('-')[-1]
                    
                    # 日付の形式を確認
                    try:
                        date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        continue  # 無効な日付形式はスキップ
                    
                    # シフトデータの保存
                    shift = Shift.query.filter_by(
                        user_name=current_user.username,
                        date=date_str
                    ).first()
                    
                    if shift:
                        # 既存のシフトデータを更新
                        if shift_type == 'morning':
                            if value != '未回答':  # 未回答の場合は既存の値を保持
                                shift.morning = value
                            else:
                                shift.morning = None
                        else:
                            if value != '未回答':  # 未回答の場合は既存の値を保持
                                shift.afternoon = value
                            else:
                                shift.afternoon = None
                        
                        # 午前も午後も未回答の場合はシフトデータを削除
                        if shift.morning is None and shift.afternoon is None:
                            db.session.delete(shift)
                    else:
                        # 新しいシフトデータを作成（未回答の場合は作成しない）
                        if value != '未回答':
                            new_shift = Shift(
                                user_name=current_user.username,
                                date=date_str,
                                morning=value if shift_type == 'morning' else None,
                                afternoon=value if shift_type == 'afternoon' else None
                            )
                            db.session.add(new_shift)
            
            db.session.commit()
            return jsonify({'category': 'success', 'message': 'シフトを保存しました'})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'シフト保存エラー: {str(e)}')
            return jsonify({'category': 'error', 'message': f'シフトの保存に失敗しました: {str(e)}'}), 500
    
    # GETリクエストの処理
    if current_user.is_authenticated:
        return render_template('index.html')
    else:
        return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。', 'success')
    return redirect(url_for('index'))

@app.route('/get_shifts/<date>')
@login_required
def get_shifts(date):
    # 未回答（None）のシフトを除外して取得
    shifts = Shift.query.filter_by(date=date).filter(
        db.or_(
            Shift.morning.isnot(None),
            Shift.afternoon.isnot(None)
        )
    ).all()
    shift_data = [shift.to_dict() for shift in shifts]
    return jsonify(shift_data)

@app.route('/viewer')
@login_required
def viewer():
    return render_template('viewer.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
