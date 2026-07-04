from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    real_name = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    fitness_level = db.Column(db.String(20))
    weekly_days = db.Column(db.Integer)
    goal_type = db.Column(db.String(20))
    role = db.Column(db.String(20), default="student", nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    workout_records = db.relationship("WorkoutRecord", backref="user", lazy=True, cascade="all, delete-orphan")
    diet_records = db.relationship("DietRecord", backref="user", lazy=True, cascade="all, delete-orphan")
    body_records = db.relationship("BodyRecord", backref="user", lazy=True, cascade="all, delete-orphan")
    workout_plans = db.relationship("WorkoutPlan", backref="user", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    admin_name = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Admin {self.username}>"


class WorkoutPlan(db.Model):
    __tablename__ = "workout_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    plan_name = db.Column(db.String(50), nullable=False)
    goal_type = db.Column(db.String(20))
    level_type = db.Column(db.String(20))
    weekly_frequency = db.Column(db.Integer)
    content = db.Column(db.Text)
    remarks = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WorkoutPlan {self.plan_name}>"


class Food(db.Model):
    __tablename__ = "foods"

    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(20))
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    carbohydrate = db.Column(db.Float)
    fat = db.Column(db.Float)
    remarks = db.Column(db.String(200))

    def __repr__(self):
        return f"<Food {self.food_name}>"


class WorkoutRecord(db.Model):
    __tablename__ = "workout_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    workout_date = db.Column(db.Date, nullable=False)
    workout_item = db.Column(db.String(50), nullable=False)
    duration_minutes = db.Column(db.Integer)
    completion_status = db.Column(db.String(20))
    calories_burned = db.Column(db.Float)
    remarks = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WorkoutRecord {self.id}>"


class DietRecord(db.Model):
    __tablename__ = "diet_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    food_name = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Float)
    total_calories = db.Column(db.Float)
    meal_type = db.Column(db.String(20))
    remarks = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DietRecord {self.id}>"


class BodyRecord(db.Model):
    __tablename__ = "body_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float)
    waist = db.Column(db.Float)
    hip = db.Column(db.Float)
    remarks = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BodyRecord {self.id}>"