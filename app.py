from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os

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

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
