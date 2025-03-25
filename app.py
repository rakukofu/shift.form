from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os  # 環境変数を扱うためのモジュール
from flask import Flask, render_template, request, redirect, url_for, flash, session  # 必要なモジュールを追加

# 管理者パスワードを環境変数から取得（デフォルト値も設定）
ADMIN_PASSWORD = '0131'  # 管理者パスワードを直接定義



app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_default_secret_key')  # 環境変数を使用することでセキュリティを向上

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response
    
# データベースの設定
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ユーザーモデルの定義
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# シフトデータモデルの定義
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# データベースを作成
with app.app_context():
    db.create_all()


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']  # フォームからパスワードを取得
        if password == ADMIN_PASSWORD:  # パスワードが正しい場合
            session['is_admin'] = True  # 管理者フラグを保存
            flash('管理者としてログインしました。', 'success')
            return redirect(url_for('admin_dashboard'))  # 管理者ページへリダイレクト
        else:
            flash('パスワードが間違っています。', 'error')
    return render_template('admin_login.html')  # ログインページを表示

@app.route('/admin')
@login_required
def admin_dashboard():
    # セッションに管理者権限がない場合はリダイレクト
    if not session.get('is_admin'):
        flash('アクセス権限がありません。', 'error')
        return redirect(url_for('index'))

    return render_template('admin.html')  # 管理者専用ページを表示

@app.route('/admin_logout')
@login_required
def admin_logout():
    session.pop('is_admin', None)  # セッションから管理者フラグを削除
    flash('管理者としてログアウトしました。', 'success')
    return redirect(url_for('index'))

@app.route('/admin/users', methods=['GET'])
@login_required
def manage_users():
    if not session.get('is_admin'):  # 管理者権限を確認
        flash('アクセス権限がありません。', 'error')
        return redirect(url_for('index'))
    
    users = User.query.all()  # データベースから全ユーザーを取得
    return render_template('manage_users.html', users=users)

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

        # 新しいユーザーをデータベースに保存
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('新しいユーザーを追加しました。', 'success')
        return redirect(url_for('manage_users'))

    return render_template('add_user.html')  # ユーザー追加フォームを表示

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not session.get('is_admin'):
        flash('アクセス権限がありません。', 'error')
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    if not user:
        flash('ユーザーが見つかりませんでした。', 'error')
        return redirect(url_for('manage_users'))

    if request.method == 'POST':
        user.username = request.form['username']
        new_password = request.form['password']
        if new_password:
            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        flash('ユーザー情報を更新しました。', 'success')
        return redirect(url_for('manage_users'))

    return render_template('edit_user.html', user=user)

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
        flash('ユーザーが見つかりませんでした。', 'error')

    return redirect(url_for('manage_users'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('ログインに成功しました。', 'success')
            return redirect(url_for('index'))  # 修正: 'viewer'から'index'に変更
        else:
            flash('ユーザー名またはパスワードが間違っています。', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')  # 修正: 無限リダイレクトを回避


@app.route('/submit', methods=['POST'])
@login_required
def submit_shift():
    user_name = current_user.username
    calendar_data = request.form.to_dict()

    print("Received calendar data:", calendar_data)  # デバッグ用ログ

    # 提出されたシフトデータを処理
    for date_key, shift_value in calendar_data.items():
        if '-morning' in date_key or '-afternoon' in date_key:
            date_str = date_key.split('-morning')[0] if '-morning' in date_key else date_key.split('-afternoon')[0]
            time_of_day = 'morning' if '-morning' in date_key else 'afternoon'

            # 「未回答」の場合はスキップ
            if shift_value.strip() == "未回答":
                print(f"スキップされました: {date_key} - {shift_value}")
                continue

            # 既存のシフトデータを取得または新規作成
            shift = Shift.query.filter_by(date=date_str, user_name=user_name).first()
            if shift:
                # 該当フィールド（午前または午後）のみ更新
                setattr(shift, time_of_day, shift_value)
            else:
                # データが存在しない場合は新しいシフトデータを作成
                shift = Shift(date=date_str, user_name=user_name)
                setattr(shift, time_of_day, shift_value)
                db.session.add(shift)

    # 変更を保存
    db.session.commit()

    flash('シフトが正常に送信されました。', 'success')
    return jsonify({'message': 'シフトが正常に送信されました。', 'category': 'success'})



    flash('シフトが正常に送信されました。', 'success')
    return jsonify({'message': 'シフトが正常に送信されました。', 'category': 'success'})

@app.route('/viewer')
@login_required
def viewer():
    return render_template('viewer.html')

@app.route('/shifts', methods=['GET'])
@login_required
def get_all_shifts():
    shifts = Shift.query.all()
    return jsonify([shift.to_dict() for shift in shifts])

@app.route('/get_shifts/<date>', methods=['GET'])
@login_required
def get_shifts(date):
    shifts = Shift.query.filter_by(date=date).all()
    return jsonify([shift.to_dict() for shift in shifts])

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404  # 修正: HTMLページを返すように変更

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500  # 修正: HTMLページを返すように変更

if __name__ == '__main__':
    app.run(debug=True)
