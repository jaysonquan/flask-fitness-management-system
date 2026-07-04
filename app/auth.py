from flask import flash, redirect, render_template, request, session, url_for

from .forms import parse_float, parse_int
from .models import Admin, User, db


def is_student_logged_in():
    return "student_id" in session


def is_admin_logged_in():
    return "admin_id" in session


def current_student():
    student_id = session.get("student_id")
    if not student_id:
        return None
    return db.session.get(User, student_id)


def require_student():
    if is_student_logged_in():
        return None
    flash("请先登录学生账号")
    return redirect(url_for("student_login"))


def require_admin():
    if is_admin_logged_in():
        return None
    flash("请先登录管理员账号")
    return redirect(url_for("admin_login"))


def register_auth_routes(app):
    @app.route("/student/register", methods=["GET", "POST"])
    def student_register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            if not username or not password:
                flash("用户名和密码不能为空")
                return redirect(url_for("student_register"))

            if User.query.filter_by(username=username).first():
                flash("该学生账号已存在")
                return redirect(url_for("student_register"))

            user = User(
                username=username,
                password=password,
                real_name=request.form.get("real_name", "").strip(),
                gender=request.form.get("gender", "").strip(),
                age=parse_int(request.form.get("age")),
                height=parse_float(request.form.get("height")),
                weight=parse_float(request.form.get("weight")),
                fitness_level=request.form.get("fitness_level", "").strip(),
                weekly_days=parse_int(request.form.get("weekly_days")),
                goal_type=request.form.get("goal_type", "").strip(),
            )
            db.session.add(user)
            db.session.commit()
            flash("注册成功，请登录")
            return redirect(url_for("student_login"))

        return render_template("register.html")

    @app.route("/student/login", methods=["GET", "POST"])
    def student_login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            user = User.query.filter_by(username=username, password=password).first()
            if not user:
                flash("用户名或密码错误")
                return redirect(url_for("student_login"))

            session.clear()
            session["student_id"] = user.id
            flash("学生登录成功")
            return redirect(url_for("student_dashboard"))

        return render_template("login.html")

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            admin = Admin.query.filter_by(username=username, password=password).first()
            if not admin:
                flash("管理员用户名或密码错误")
                return redirect(url_for("admin_login"))

            session.clear()
            session["admin_id"] = admin.id
            flash("管理员登录成功")
            return redirect(url_for("admin_dashboard"))

        return render_template("admin/login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("已退出登录")
        return redirect(url_for("index"))
