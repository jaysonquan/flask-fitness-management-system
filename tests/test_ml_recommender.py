from datetime import date
from types import SimpleNamespace
import unittest

from ml_recommender import analyze_student_profile


class MLRecommenderTest(unittest.TestCase):
    def test_low_activity_student_is_classified_as_training_insufficient(self):
        user = SimpleNamespace(
            height=170,
            weight=76,
            weekly_days=1,
            goal_type="减脂",
            fitness_level="新手",
        )
        body_records = [
            SimpleNamespace(record_date=date(2026, 6, 1), weight=78, bmi=None),
            SimpleNamespace(record_date=date(2026, 6, 15), weight=76, bmi=None),
        ]

        result = analyze_student_profile(user, body_records, [], [])

        self.assertEqual(result["algorithm"], "本地可训练健康分析模型")
        self.assertEqual(result["profile"]["label"], "训练不足型")
        self.assertEqual(result["profile_type"], "训练不足型")
        self.assertGreater(result["training_sample_count"], 0)
        self.assertIn("每周训练天数偏低", result["profile"]["reasons"])

    def test_high_calorie_diet_reports_diet_risk(self):
        user = SimpleNamespace(
            height=170,
            weight=76,
            weekly_days=3,
            goal_type="减脂",
            fitness_level="一般",
        )
        diet_records = [
            SimpleNamespace(record_date=date(2026, 6, 1), total_calories=3200, meal_type="早餐"),
            SimpleNamespace(record_date=date(2026, 6, 1), total_calories=1800, meal_type="晚餐"),
            SimpleNamespace(record_date=date(2026, 6, 2), total_calories=3500, meal_type="午餐"),
        ]

        result = analyze_student_profile(user, [], [], diet_records)

        self.assertEqual(result["diet_risk"]["level"], "高风险")
        self.assertIn("热量偏高", result["diet_risk"]["labels"])
        self.assertIn("与减脂目标不匹配", result["diet_risk"]["labels"])

    def test_regular_training_and_weight_loss_predicts_downward_trend(self):
        user = SimpleNamespace(
            height=168,
            weight=66,
            weekly_days=4,
            goal_type="减脂",
            fitness_level="一般",
        )
        body_records = [
            SimpleNamespace(record_date=date(2026, 6, 1), weight=70, bmi=None),
            SimpleNamespace(record_date=date(2026, 6, 15), weight=66, bmi=None),
        ]
        workout_records = [
            SimpleNamespace(
                workout_date=date(2026, 6, 2),
                duration_minutes=45,
                calories_burned=320,
                completion_status="已完成",
            ),
            SimpleNamespace(
                workout_date=date(2026, 6, 5),
                duration_minutes=50,
                calories_burned=360,
                completion_status="已完成",
            ),
            SimpleNamespace(
                workout_date=date(2026, 6, 9),
                duration_minutes=40,
                calories_burned=300,
                completion_status="已完成",
            ),
        ]
        diet_records = [
            SimpleNamespace(record_date=date(2026, 6, 1), total_calories=1800, meal_type="早餐"),
            SimpleNamespace(record_date=date(2026, 6, 1), total_calories=500, meal_type="午餐"),
            SimpleNamespace(record_date=date(2026, 6, 2), total_calories=1900, meal_type="晚餐"),
        ]

        result = analyze_student_profile(user, body_records, workout_records, diet_records)

        self.assertEqual(result["training_trend"]["label"], "体重可能下降")
        self.assertGreaterEqual(result["training_trend"]["confidence"], 60)
        self.assertTrue(result["suggestions"])

    def test_insufficient_body_records_returns_data_insufficient_trend(self):
        user = SimpleNamespace(
            height=168,
            weight=67,
            weekly_days=3,
            goal_type="保持体态",
            fitness_level="一般",
        )

        result = analyze_student_profile(user, [], [], [])

        self.assertEqual(result["training_trend"]["label"], "数据不足，暂不预测")
        self.assertIn("饮食记录不足", result["diet_risk"]["labels"])


if __name__ == "__main__":
    unittest.main()
