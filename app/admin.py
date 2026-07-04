from flask import flash, redirect, render_template, request, url_for

from .auth import require_admin
from .forms import parse_float
from .models import Food, db


def register_admin_routes(app):
    @app.route("/admin/dashboard")
    def admin_dashboard():
        redirect_response = require_admin()
        if redirect_response:
            return redirect_response
        return render_template("admin/dashboard.html")

    @app.route("/admin/foods")
    def foods():
        redirect_response = require_admin()
        if redirect_response:
            return redirect_response

        food_list = Food.query.order_by(Food.id.desc()).all()
        return render_template("admin/food.html", foods=food_list)

    @app.route("/admin/foods/add", methods=["GET", "POST"])
    def add_food():
        redirect_response = require_admin()
        if redirect_response:
            return redirect_response

        if request.method == "POST":
            food_name = request.form.get("food_name", "").strip()
            if not food_name:
                flash("食物名称不能为空")
                return redirect(url_for("add_food"))

            try:
                food = Food(
                    food_name=food_name,
                    category=request.form.get("category", "").strip(),
                    calories=parse_float(request.form.get("calories")),
                    protein=parse_float(request.form.get("protein")),
                    carbohydrate=parse_float(request.form.get("carbohydrate")),
                    fat=parse_float(request.form.get("fat")),
                    remarks=request.form.get("remarks", "").strip(),
                )
            except ValueError:
                flash("食物营养数据格式错误")
                return redirect(url_for("add_food"))

            db.session.add(food)
            db.session.commit()
            flash("食物添加成功")
            return redirect(url_for("foods"))

        return render_template("admin/food_form.html")

    @app.route("/admin/foods/delete/<int:food_id>")
    def delete_food(food_id):
        redirect_response = require_admin()
        if redirect_response:
            return redirect_response

        food = db.session.get(Food, food_id)
        if food:
            db.session.delete(food)
            db.session.commit()
            flash("食物删除成功")
        else:
            flash("未找到该食物")

        return redirect(url_for("foods"))
