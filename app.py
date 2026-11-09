from random import choice, random

from flask import Flask, flash, redirect, render_template, request
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_migrate import Migrate
from models import Task, User, db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://db_user:db_password@localhost/todo_db"  # 接続先DBを定義
app.secret_key = "deadbeef"
db.init_app(app)
Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", title="ユーザ登録")

    if (
        request.form["id"] == ""
        or request.form["password"] == ""
        or request.form["lastname"] == ""
        or request.form["firstname"] == ""
    ):
        flash("入力されていない項目があります")
        return render_template("register.html", title="ユーザ登録")
    if User.query.get(request.form["id"]) is not None:
        flash("ユーザを登録できません")
        return render_template("register.html", title="ユーザ登録")

    user = User(
        id=request.form["id"],
        password=request.form["password"],
        lastname=request.form["lastname"],
        firstname=request.form["firstname"],
    )
    db.session.add(user)
    db.session.commit()
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "GET":
        return render_template("login.html", title="ログイン")
    #
    user = User.query.get(request.form["id"])

    if user is not None and user.verify_password(request.form["password"]):
        login_user(user)
        return redirect("/")
    #
    flash("ユーザIDかパスワードが誤っています")
    return redirect("/login")


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")


@app.route("/")
@login_required
def index():
    my_tasks = Task.query.filter_by(user=current_user)
    shared_tasks = Task.query.filter(Task.user_id.in_(f.id for f in current_user.followees) & Task.is_shared)
    return render_template(
        "index.html", title="ホーム", my_tasks=my_tasks, shared_tasks=shared_tasks
    )  # 2種類のタスクをテンプレートに渡す


@app.route("/create", methods=["GET", "POST"])  # methodsに"GET"を追加
@login_required
def create():
    task = Task(
        user=current_user,
        name=request.form["name"],
        deadline=request.form["deadline"],
        is_shared=request.form.get("is_shared") is not None,
    )
    db.session.add(task)
    db.session.commit()
    return redirect("/")


@app.route("/update/<int:task_id>", methods=["GET", "POST"])
@login_required
def update(task_id):
    task = Task.query.get(task_id)
    #
    if task is None or task.user != current_user:
        flash("存在しないタスクです")
        return redirect("/")

    if request.method == "GET":
        return render_template("update.html", title="更新", task=task)

    task.name = request.form["name"]
    task.deadline = request.form["deadline"]
    task.is_shared = request.form.get("is_shared") is not None
    db.session.commit()
    return redirect("/")


@app.route("/delete/<int:task_id>", methods=["GET", "POST"])
@login_required
def delete(task_id):  # この行は自身で修正している可能性が高い
    task = Task.query.get(task_id)
    #
    if task is None or task.user != current_user:
        flash("存在しないタスクです")
        return redirect("/")

    if request.method == "GET":
        return render_template("/delete.html", title="削除", task=task)

    db.session.delete(task)
    db.session.commit()
    return redirect("/")


@app.route("/users")
@login_required
def users():
    users = User.query.all()
    users.remove(current_user)  # 自身を除く
    return render_template("users.html", title="ユーザ一覧", users=users)


@app.route("/follow/<string:user_id>")
@login_required
def follow(user_id):
    user = User.query.get(user_id)  # フォローしようとしているユーザ
    if user == current_user:  # 自身をフォローさせない
        flash("自身をフォローできません")
    elif current_user in user.followers:  # 既にフォローしている場合
        flash("既にフォローしています")
    else:  # フォローしていなければ
        user.followers.append(current_user)  # ユーザのフォロワーに追加
        db.session.commit()  # DBに反映
    return redirect("/users")


@app.route("/unfollow/<string:user_id>")
@login_required
def unfollow(user_id):
    followee = User.query.get(user_id)
    if followee in current_user.followees:
        current_user.followees.remove(followee)
        db.session.commit()
    else:
        flash("フォローしていません")
    return redirect("/users")


@app.route("/rand")
def rand():
    r = random()
    label = "larger"
    if r < 0.3:
        label = "smaller"
    elif r <= 0.7:
        label = "medium"
    return f"{r=:.3f} {label}"


@app.route("/template")
def template():
    return render_template("template.html", greeting="hello", title="あいさつ")


@app.route("/template_list")
def template_list():
    students = []
    for n in range(1, 101):
        students.append(f"2xG2{n:03d}")

    return render_template("template_list.html", students=students, title="学生番号リスト")


@app.route("/template_dict")
def template_dict():
    students = {}
    for n in range(1, 101):
        students[f"2xG2{n:03d}"] = choice(["A", "B", "C"])

    return render_template("template_dict.html", classes=["A", "C"], students=students, title="学生ごとのクラス分け")
