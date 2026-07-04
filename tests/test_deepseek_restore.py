import unittest
import tempfile
from pathlib import Path


class DeepSeekRestoreTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tempdir.name) / "fitness_test.db"

        from app import create_app
        from models import User, db

        self.db = db
        self.User = User
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            }
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_ai_recommend_requires_student_login(self):
        response = self.client.get("/ai_recommend", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/student/login", response.headers["Location"])

    def test_logged_in_student_can_view_ai_recommendations(self):
        with self.app.app_context():
            student = self.User(
                username="ai_student",
                password="secret",
                fitness_level="新手",
                weekly_days=3,
                goal_type="减脂",
            )
            self.db.session.add(student)
            self.db.session.commit()
            student_id = student.id

        with self.client.session_transaction() as session:
            session["student_id"] = student_id

        response = self.client.get("/ai_recommend")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("智能健身饮食推荐", body)
        self.assertIn("机器学习分析结果", body)
        self.assertIn("本地可训练健康分析模型", body)
        self.assertIn("用户状态分类", body)
        self.assertIn("饮食风险分析", body)
        self.assertIn("训练效果趋势预测", body)
        self.assertIn("减脂", body)
        self.assertIn("每周 3 次", body)


if __name__ == "__main__":
    unittest.main()
