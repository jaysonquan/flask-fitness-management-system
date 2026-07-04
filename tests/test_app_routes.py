import tempfile
import unittest
from io import BytesIO
from pathlib import Path


class FitnessAppRoutesTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tempdir.name) / "fitness_test.db"

        from app import create_app
        from models import Admin, Food, User, WorkoutPlan, db

        self.db = db
        self.Admin = Admin
        self.Food = Food
        self.User = User
        self.WorkoutPlan = WorkoutPlan
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
                "WTF_CSRF_ENABLED": False,
            }
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            db.session.add(
                Admin(username="admin", password="123456", admin_name="系统管理员")
            )
            db.session.commit()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_home_page_links_to_student_and_admin_login(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("学生注册", body)
        self.assertIn("学生登录", body)
        self.assertIn("管理员登录", body)

    def test_student_can_register_login_and_open_dashboard(self):
        register = self.client.post(
            "/student/register",
            data={
                "username": "student1",
                "password": "secret",
                "real_name": "张三",
                "gender": "男",
                "age": "20",
                "height": "178",
                "weight": "70",
                "fitness_level": "新手",
                "weekly_days": "3",
                "goal_type": "增肌",
            },
            follow_redirects=False,
        )
        self.assertEqual(register.status_code, 302)

        login = self.client.post(
            "/student/login",
            data={"username": "student1", "password": "secret"},
            follow_redirects=True,
        )
        body = login.get_data(as_text=True)
        self.assertEqual(login.status_code, 200)
        self.assertIn("学生主页", body)
        self.assertIn("张三", body)

    def test_logged_in_student_can_create_records_and_view_chart(self):
        with self.app.app_context():
            student = self.User(username="student2", password="secret")
            self.db.session.add(student)
            self.db.session.commit()
            student_id = student.id

        with self.client.session_transaction() as session:
            session["student_id"] = student_id

        workout = self.client.post(
            "/student/workouts/add",
            data={
                "workout_date": "2026-06-01",
                "workout_item": "跑步",
                "duration_minutes": "30",
                "completion_status": "已完成",
                "calories_burned": "200",
                "remarks": "状态不错",
            },
            follow_redirects=True,
        )
        self.assertIn("跑步", workout.get_data(as_text=True))

        diet = self.client.post(
            "/student/diets/add",
            data={
                "record_date": "2026-06-01",
                "food_name": "鸡胸肉",
                "quantity": "150",
                "total_calories": "250",
                "meal_type": "午餐",
                "remarks": "高蛋白",
            },
            follow_redirects=True,
        )
        self.assertIn("鸡胸肉", diet.get_data(as_text=True))

        body_record = self.client.post(
            "/student/body/add",
            data={
                "record_date": "2026-06-01",
                "weight": "70.5",
                "bmi": "22.2",
                "waist": "80",
                "hip": "92",
                "remarks": "晨起空腹",
            },
            follow_redirects=True,
        )
        self.assertIn("70.5", body_record.get_data(as_text=True))

        chart = self.client.get("/student/chart")
        chart_body = chart.get_data(as_text=True)
        self.assertEqual(chart.status_code, 200)
        self.assertIn("2026-06-01", chart_body)
        self.assertIn("70.5", chart_body)

    def test_admin_can_manage_foods(self):
        login = self.client.post(
            "/admin/login",
            data={"username": "admin", "password": "123456"},
            follow_redirects=True,
        )
        self.assertIn("管理员", login.get_data(as_text=True))

        response = self.client.post(
            "/admin/foods/add",
            data={
                "food_name": "燕麦",
                "category": "主食",
                "calories": "380",
                "protein": "13",
                "carbohydrate": "67",
                "fat": "7",
                "remarks": "早餐",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("燕麦", response.get_data(as_text=True))

    def test_workout_plan_uses_model_fields_consistently(self):
        with self.app.app_context():
            student = self.User(username="planner", password="secret")
            self.db.session.add(student)
            self.db.session.commit()
            student_id = student.id

        with self.client.session_transaction() as session:
            session["student_id"] = student_id

        response = self.client.post(
            "/student/workout-plans/add",
            data={
                "plan_name": "三天增肌计划",
                "goal_type": "增肌",
                "level_type": "新手",
                "weekly_frequency": "3",
                "content": "深蹲、卧推、划船循环训练",
                "remarks": "每次训练后拉伸",
            },
            follow_redirects=True,
        )

        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("三天增肌计划", body)
        self.assertIn("深蹲、卧推、划船循环训练", body)

    def test_student_can_create_diet_records_from_image_recognition(self):
        with self.app.app_context():
            student = self.User(username="photo_diet", password="secret")
            foods = [
                self.Food(food_name="米饭", calories=116),
                self.Food(food_name="鸡胸肉", calories=165),
                self.Food(food_name="西兰花", calories=34),
            ]
            self.db.session.add(student)
            self.db.session.add_all(foods)
            self.db.session.commit()
            student_id = student.id

        with self.client.session_transaction() as session:
            session["student_id"] = student_id

        preview = self.client.post(
            "/student/diets/image-recognition",
            data={
                "action": "recognize",
                "meal_image": (
                    BytesIO(b"fake image bytes"),
                    "rice_chicken_broccoli.jpg",
                ),
                "record_date": "2026-06-01",
                "meal_type": "午餐",
            },
            content_type="multipart/form-data",
        )
        preview_body = preview.get_data(as_text=True)

        self.assertEqual(preview.status_code, 200)
        self.assertIn("图片识别结果", preview_body)
        self.assertIn("米饭", preview_body)
        self.assertIn("鸡胸肉", preview_body)
        self.assertIn("西兰花", preview_body)

        saved = self.client.post(
            "/student/diets/image-recognition",
            data={
                "action": "save",
                "record_date": "2026-06-01",
                "meal_type": "午餐",
                "food_name": ["米饭", "鸡胸肉", "西兰花"],
                "quantity": ["180", "120", "80"],
                "calories_per_100g": ["116", "165", "34"],
            },
            follow_redirects=True,
        )
        saved_body = saved.get_data(as_text=True)

        self.assertEqual(saved.status_code, 200)
        self.assertIn("已根据图片识别结果保存 3 条饮食记录", saved_body)
        self.assertIn("米饭", saved_body)
        self.assertIn("鸡胸肉", saved_body)
        self.assertIn("西兰花", saved_body)

    def test_image_recognition_preview_shows_ai_success_status(self):
        class VisionClientStub:
            def recognize(self, filename, image_bytes, mime_type):
                return [
                    {
                        "food_name": "白米饭",
                        "estimated_grams": 160,
                        "confidence": "高",
                        "reason": "图中为一碗米饭",
                    }
                ]

        with self.app.app_context():
            student = self.User(username="vision_user", password="secret")
            self.db.session.add(student)
            self.db.session.add(self.Food(food_name="米饭", calories=116))
            self.db.session.commit()
            student_id = student.id

        self.app.config["VISION_CLIENT"] = VisionClientStub()
        with self.client.session_transaction() as session:
            session["student_id"] = student_id

        response = self.client.post(
            "/student/diets/image-recognition",
            data={
                "action": "recognize",
                "meal_image": (BytesIO(b"fake image bytes"), "meal.jpg"),
                "record_date": "2026-06-01",
                "meal_type": "午餐",
            },
            content_type="multipart/form-data",
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("AI视觉识别成功", body)
        self.assertIn("米饭", body)
        self.assertIn("图中为一碗米饭", body)


if __name__ == "__main__":
    unittest.main()
