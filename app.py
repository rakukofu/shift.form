from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

# 環境変数と設定
ADMIN_PASSWORD = '0131'
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_default_secret_key')

# データベース接続設定
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/app.db')  # PostgreSQL の URL を環境変数から取得
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初期化
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/viewer')
@login_required
def viewer():
    return render_template('viewer.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('ログインに成功しました。', 'success')
            return redirect(url_for('index'))
        else:
            flash('ユーザー名またはパスワードが間違っています。', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。', 'success')
    return redirect(url_for('login'))

@app.route('/get_shifts/<date>')
@login_required
def get_shifts(date):
    shifts = Shift.query.filter_by(date=date).all()
    return jsonify([shift.to_dict() for shift in shifts])

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    shifts = []
    for key, value in request.form.items():
        if 'morning' in key or 'afternoon' in key:
            date, time = key.split('-')[0:2], key.split('-')[-1]
            user_name = current_user.username
            shift = Shift(date='-'.join(date), user_name=user_name, morning=value if 'morning' in key else None,
                          afternoon=value if 'afternoon' in key else None)
            shifts.append(shift)

    db.session.bulk_save_objects(shifts)
    db.session.commit()
    flash('シフトが正常に保存されました。', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not session.get('is_admin'):
        flash('アクセス権限がありません。', 'error')
        return redirect(url_for('login'))
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
