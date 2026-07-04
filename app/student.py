from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .auth import current_student, require_student
from .food_image_recognizer import recognize_meal_image_detailed
from .forms import parse_date, parse_float, parse_int
from .ml_recommender import analyze_student_profile
from .models import BodyRecord, DietRecord, Food, WorkoutPlan, WorkoutRecord, db
from .utils import build_ai_recommendations, vision_config_notice


def register_student_routes(app):
    @app.route("/student/dashboard")
    def student_dashboard():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        user = current_student()
        if not user:
            session.clear()
            flash("学生账号不存在，请重新登录")
            return redirect(url_for("student_login"))

        return render_template("student/dashboard.html", user=user)

    @app.route("/edit_profile", methods=["GET", "POST"])
    def edit_profile():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        user = current_student()
        if request.method == "POST":
            user.real_name = request.form.get("real_name", "").strip()
            user.gender = request.form.get("gender", "").strip()
            user.age = parse_int(request.form.get("age"))
            user.height = parse_float(request.form.get("height"))
            user.weight = parse_float(request.form.get("weight"))
            user.fitness_level = request.form.get("fitness_level", "").strip()
            user.weekly_days = parse_int(request.form.get("weekly_days"))
            user.goal_type = request.form.get("goal_type", "").strip()
            db.session.commit()
            flash("个人资料已保存")
            return redirect(url_for("student_dashboard"))

        return render_template("student/profile.html", user=user)

    @app.route("/student/workouts")
    def workout_records():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        user = current_student()
        records = (
            WorkoutRecord.query.filter_by(user_id=user.id)
            .order_by(WorkoutRecord.workout_date.desc())
            .all()
        )
        return render_template("student/training.html", user=user, records=records)

    @app.route("/student/workouts/add", methods=["GET", "POST"])
    def add_workout_record():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        if request.method == "POST":
            workout_date_str = request.form.get("workout_date", "").strip()
            workout_item = request.form.get("workout_item", "").strip()

            if not workout_date_str or not workout_item:
                flash("训练日期和训练项目不能为空")
                return redirect(url_for("add_workout_record"))

            try:
                workout_date = parse_date(workout_date_str)
                record = WorkoutRecord(
                    user_id=session["student_id"],
                    workout_date=workout_date,
                    workout_item=workout_item,
                    duration_minutes=parse_int(request.form.get("duration_minutes")),
                    completion_status=request.form.get("completion_status", "").strip(),
                    calories_burned=parse_float(request.form.get("calories_burned")),
                    remarks=request.form.get("remarks", "").strip(),
                )
            except ValueError:
                flash("训练记录中的数字或日期格式错误")
                return redirect(url_for("add_workout_record"))

            db.session.add(record)
            db.session.commit()
            flash("训练记录添加成功")
            return redirect(url_for("workout_records"))

        return render_template("student/training_form.html")

    @app.route("/student/diets")
    def diet_records():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        user = current_student()
        records = (
            DietRecord.query.filter_by(user_id=user.id)
            .order_by(DietRecord.record_date.desc())
            .all()
        )
        return render_template("student/diet.html", user=user, records=records)

    @app.route("/student/diets/add", methods=["GET", "POST"])
    def add_diet_record():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        if request.method == "POST":
            record_date_str = request.form.get("record_date", "").strip()
            food_name = request.form.get("food_name", "").strip()

            if not record_date_str or not food_name:
                flash("饮食日期和食物名称不能为空")
                return redirect(url_for("add_diet_record"))

            try:
                record = DietRecord(
                    user_id=session["student_id"],
                    record_date=parse_date(record_date_str),
                    food_name=food_name,
                    quantity=parse_float(request.form.get("quantity")),
                    total_calories=parse_float(request.form.get("total_calories")),
                    meal_type=request.form.get("meal_type", "").strip(),
                    remarks=request.form.get("remarks", "").strip(),
                )
            except ValueError:
                flash("饮食记录中的数字或日期格式错误")
                return redirect(url_for("add_diet_record"))

            db.session.add(record)
            db.session.commit()
            flash("饮食记录添加成功")
            return redirect(url_for("diet_records"))

        return render_template("student/diet_form.html")

    @app.route("/student/diets/image-recognition", methods=["GET", "POST"])
    def image_diet_recognition():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        if request.method == "POST":
            action = request.form.get("action", "recognize")
            record_date = request.form.get("record_date", "").strip()
            meal_type = request.form.get("meal_type", "").strip()

            if action == "save":
                return save_image_diet_records(record_date, meal_type)

            if not record_date:
                flash("饮食日期不能为空")
                return redirect(url_for("image_diet_recognition"))

            upload = request.files.get("meal_image")
            filename = upload.filename if upload else ""
            if not filename:
                flash("请先上传餐食图片")
                return redirect(url_for("image_diet_recognition"))

            foods = Food.query.order_by(Food.food_name.asc()).all()
            recognition_result = recognize_meal_image_detailed(
                filename,
                foods,
                image_bytes=upload.read(),
                mime_type=upload.mimetype,
                vision_client=current_app.config.get("VISION_CLIENT"),
            )
            return render_template(
                "student/image_diet_recognition.html",
                recognized_items=recognition_result["items"],
                recognition_result=recognition_result,
                record_date=record_date,
                meal_type=meal_type,
                vision_notice=(
                    ""
                    if current_app.config.get("VISION_CLIENT")
                    else vision_config_notice()
                ),
            )

        return render_template(
            "student/image_diet_recognition.html",
            recognized_items=[],
            recognition_result=None,
            record_date="",
            meal_type="",
            vision_notice=(
                "" if current_app.config.get("VISION_CLIENT") else vision_config_notice()
            ),
        )

    @app.route("/student/body")
    def body_records():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        user = current_student()
        records = (
            BodyRecord.query.filter_by(user_id=user.id)
            .order_by(BodyRecord.record_date.desc())
            .all()
        )
        return render_template("student/body.html", user=user, records=records)

    @app.route("/student/body/add", methods=["GET", "POST"])
    def add_body_record():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        if request.method == "POST":
            record_date_str = request.form.get("record_date", "").strip()
            weight = request.form.get("weight", "").strip()

            if not record_date_str or not weight:
                flash("记录日期和体重不能为空")
                return redirect(url_for("add_body_record"))

            try:
                record = BodyRecord(
                    user_id=session["student_id"],
                    record_date=parse_date(record_date_str),
                    weight=parse_float(weight),
                    bmi=parse_float(request.form.get("bmi")),
                    waist=parse_float(request.form.get("waist")),
                    hip=parse_float(request.form.get("hip")),
                    remarks=request.form.get("remarks", "").strip(),
                )
            except ValueError:
                flash("身体指标中的数字或日期格式错误")
                return redirect(url_for("add_body_record"))

            db.session.add(record)
            db.session.commit()
            flash("身体指标添加成功")
            return redirect(url_for("body_records"))

        return render_template("student/body_form.html")

    @app.route("/student/chart")
    def student_chart():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        user = current_student()
        records = (
            BodyRecord.query.filter_by(user_id=user.id)
            .order_by(BodyRecord.record_date.asc())
            .all()
        )
        dates = [record.record_date.isoformat() for record in records]
        weights = [record.weight for record in records]
        return render_template("student/chart.html", user=user, dates=dates, weights=weights)

    @app.route("/ai_recommend")
    def ai_recommend():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        user = current_student()
        if not user:
            session.clear()
            flash("学生账号不存在，请重新登录")
            return redirect(url_for("student_login"))

        body_records = (
            BodyRecord.query.filter_by(user_id=user.id)
            .order_by(BodyRecord.record_date.asc())
            .all()
        )
        workout_records = WorkoutRecord.query.filter_by(user_id=user.id).all()
        diet_records = DietRecord.query.filter_by(user_id=user.id).all()
        ml_analysis = analyze_student_profile(
            user, body_records, workout_records, diet_records
        )
        recommendations = build_ai_recommendations(user)
        return render_template(
            "student/recommend.html",
            user=user,
            recommendations=recommendations,
            ml_analysis=ml_analysis,
        )

    @app.route("/student/workout-plans")
    def workout_plans():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        user = current_student()
        plans = (
            WorkoutPlan.query.filter_by(user_id=user.id)
            .order_by(WorkoutPlan.created_at.desc())
            .all()
        )
        return render_template("student/plan.html", user=user, plans=plans)

    @app.route("/student/workout-plans/add", methods=["GET", "POST"])
    def add_workout_plan():
        redirect_response = require_student()
        if redirect_response:
            return redirect_response

        if request.method == "POST":
            plan_name = request.form.get("plan_name", "").strip()
            if not plan_name:
                flash("计划名称不能为空")
                return redirect(url_for("add_workout_plan"))

            try:
                plan = WorkoutPlan(
                    user_id=session["student_id"],
                    plan_name=plan_name,
                    goal_type=request.form.get("goal_type", "").strip(),
                    level_type=request.form.get("level_type", "").strip(),
                    weekly_frequency=parse_int(request.form.get("weekly_frequency")),
                    content=request.form.get("content", "").strip(),
                    remarks=request.form.get("remarks", "").strip(),
                )
            except ValueError:
                flash("训练频率格式错误")
                return redirect(url_for("add_workout_plan"))

            db.session.add(plan)
            db.session.commit()
            flash("健身计划添加成功")
            return redirect(url_for("workout_plans"))

        return render_template("student/plan_form.html")


def save_image_diet_records(record_date_str, meal_type):
    if not record_date_str:
        flash("饮食日期不能为空")
        return redirect(url_for("image_diet_recognition"))

    food_names = request.form.getlist("food_name")
    quantities = request.form.getlist("quantity")
    calories_per_100g_values = request.form.getlist("calories_per_100g")
    recognition_sources = request.form.getlist("recognition_source")
    reasons = request.form.getlist("reason")

    try:
        record_date = parse_date(record_date_str)
        saved_count = 0
        for index, raw_food_name in enumerate(food_names):
            food_name = raw_food_name.strip()
            if not food_name:
                continue

            quantity_value = quantities[index] if index < len(quantities) else ""
            calories_value = (
                calories_per_100g_values[index]
                if index < len(calories_per_100g_values)
                else ""
            )
            recognition_source = (
                recognition_sources[index]
                if index < len(recognition_sources) and recognition_sources[index]
                else "手动确认"
            )
            reason = reasons[index] if index < len(reasons) and reasons[index] else "用户确认"
            quantity = parse_float(quantity_value)
            calories_per_100g = parse_float(calories_value)
            total_calories = None
            if quantity is not None and calories_per_100g is not None:
                total_calories = round(quantity * calories_per_100g / 100, 1)

            db.session.add(
                DietRecord(
                    user_id=session["student_id"],
                    record_date=record_date,
                    food_name=food_name,
                    quantity=quantity,
                    total_calories=total_calories,
                    meal_type=meal_type,
                    remarks=f"{recognition_source}估算，已由用户确认：{reason[:60]}",
                )
            )
            saved_count += 1
    except ValueError:
        flash("图片识别饮食记录中的数字或日期格式错误")
        return redirect(url_for("image_diet_recognition"))

    if not saved_count:
        flash("没有可保存的识别结果")
        return redirect(url_for("image_diet_recognition"))

    db.session.commit()
    flash(f"已根据图片识别结果保存 {saved_count} 条饮食记录")
    return redirect(url_for("diet_records"))
