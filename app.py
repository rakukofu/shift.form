from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv

# 環境変数と設定
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
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
@login_required
def admin_dashboard():
    if not session.get('is_admin'):
        flash('アクセス権限がありません。', 'error')
        return redirect(url_for('admin_login'))  
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')  
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('管理者としてログインしました。', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('パスワードが間違っています。', 'error')
    return render_template('admin_login.html')

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if not session.get('is_admin'):
        flash('アクセス権限がありません。', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('新しいユーザーを追加しました。', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_user.html')
    
@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not session.get('is_admin'):
        flash('アクセス権限がありません。', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get(user_id)
    if not user:
        flash('指定されたユーザーが見つかりません。', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        user.username = request.form['username']
        new_password = request.form['password']
        if new_password:
            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        flash('ユーザー情報を更新しました。', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_users.html', user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not session.get('is_admin'):
        flash('アクセス権限がありません。', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'ユーザー {user.username} を削除しました。', 'success')
    else:
        flash('指定されたユーザーが見つかりません。', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form:
            # ログイン処理
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                flash('ログインに成功しました。', 'success')
                return redirect(url_for('index'))
            else:
                flash('ユーザー名またはパスワードが間違っています。', 'error')
        elif current_user.is_authenticated:
            # シフト送信処理
            date = request.form['date']
            user_name = request.form['user_name']
            morning = request.form['morning']
            afternoon = request.form['afternoon']
            
            new_shift = Shift(date=date, user_name=user_name, morning=morning, afternoon=afternoon)
            db.session.add(new_shift)
            db.session.commit()
            flash('シフトを送信しました。', 'success')
            return redirect(url_for('index'))
    
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
    shifts = Shift.query.filter_by(date=date).all()
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
