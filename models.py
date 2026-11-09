from datetime import datetime  # 日時を扱うために必要なライブラリ

from flask_login import UserMixin  # ユーザに必要なメソッドを扱うMixin
from flask_sqlalchemy import SQLAlchemy  # DBを扱うために必要なライブラリ
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()  # DBを扱うインスタンスを生成


follows = db.Table(  # ユーザ間のフォロー関係を示す中間テーブル
    "follows",
    # フォローしているユーザのID
    db.Column("follower_id", db.String(255), db.ForeignKey("users.id"), primary_key=True),
    # フォローされているユーザのID
    db.Column("followee_id", db.String(255), db.ForeignKey("users.id"), primary_key=True),
)


class Task(db.Model):
    # タスクを登録するためのモデル
    __tablename__ = "tasks"  # DB内部で使用する名前（テーブル名）

    id = db.Column(db.Integer, primary_key=True)  # 一意なID（数字）
    user_id = db.Column(db.String(255), db.ForeignKey("users.id"), nullable=False)  # どのユーザのタスクか
    name = db.Column(db.String(255), nullable=False)  # タスク名
    deadline = db.Column(db.DateTime, nullable=False)  # 締切
    is_shared = db.Column(db.Boolean, nullable=False, default=False)  # 共有フラグ
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)  # 作成日時


class User(UserMixin, db.Model):
    # ユーザを登録するためのモデル
    __tablename__ = "users"

    id = db.Column(db.String(255), primary_key=True)  # ユーザID（文字列）
    password_hash = db.Column(db.String(162), nullable=False)  # パスワードのハッシュ
    lastname = db.Column(db.String(255), nullable=False)  # 姓
    firstname = db.Column(db.String(255), nullable=False)  # 名
    tasks = db.relationship("Task", backref="user", lazy=True)  # このユーザが管理するタスクたちを示す
    followees = db.relationship(  # このユーザのフォロイーたちを示す
        "User",
        secondary=follows,
        primaryjoin=(follows.c.follower_id == id),
        secondaryjoin=(follows.c.followee_id == id),
        backref=db.backref("followers"),
        lazy=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)  # 作成日時

    @property  # パスワードを読ませないための対策
    def password(self):
        message = "パスワードは読めません"
        raise AttributeError(message)

    @password.setter  # パスワード設定時にハッシュに変換
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):  # パスワードの検証
        return check_password_hash(self.password_hash, password)
