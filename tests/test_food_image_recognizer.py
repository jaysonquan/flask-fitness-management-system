import unittest

from food_image_recognizer import recognize_meal_image, recognize_meal_image_detailed


class FoodImageRecognizerTest(unittest.TestCase):
    def test_demo_meal_image_returns_estimated_food_items(self):
        items = recognize_meal_image("rice_chicken_broccoli.jpg", [])

        names = [item["food_name"] for item in items]
        self.assertIn("米饭", names)
        self.assertIn("鸡胸肉", names)
        self.assertIn("西兰花", names)

        rice = next(item for item in items if item["food_name"] == "米饭")
        self.assertEqual(rice["estimated_grams"], 180)
        self.assertEqual(rice["confidence"], "中")
        self.assertGreater(rice["estimated_calories"], 0)

    def test_food_library_overrides_default_calories(self):
        class FoodStub:
            food_name = "米饭"
            calories = 130

        items = recognize_meal_image("rice.jpg", [FoodStub()])
        rice = items[0]

        self.assertEqual(rice["calories_per_100g"], 130)
        self.assertEqual(rice["source"], "食物库")

    def test_vision_client_result_is_matched_to_food_library(self):
        class FoodStub:
            def __init__(self, food_name, calories):
                self.food_name = food_name
                self.calories = calories

        class VisionClientStub:
            def recognize(self, filename, image_bytes, mime_type):
                return [
                    {
                        "food_name": "白米饭",
                        "estimated_grams": 160,
                        "confidence": "中",
                        "reason": "图片中有一小碗米饭",
                    },
                    {
                        "food_name": "鸡肉",
                        "estimated_grams": 100,
                        "confidence": "中",
                        "reason": "图片中有掌心大小肉类",
                    },
                ]

        foods = [FoodStub("米饭", 116), FoodStub("鸡胸肉", 165)]
        items = recognize_meal_image(
            "random.jpg",
            foods,
            image_bytes=b"fake image",
            mime_type="image/jpeg",
            vision_client=VisionClientStub(),
        )

        self.assertEqual([item["food_name"] for item in items], ["米饭", "鸡胸肉"])
        self.assertEqual(items[0]["estimated_grams"], 160)
        self.assertEqual(items[0]["calories_per_100g"], 116)
        self.assertEqual(items[0]["recognition_source"], "AI视觉识别")
        self.assertIn("一小碗", items[0]["reason"])

    def test_detailed_result_marks_successful_vision_mode(self):
        class VisionClientStub:
            def recognize(self, filename, image_bytes, mime_type):
                return [
                    {
                        "food_name": "米饭",
                        "estimated_grams": 150,
                        "confidence": "高",
                        "reason": "图中主体为米饭",
                    }
                ]

        result = recognize_meal_image_detailed(
            "meal.jpg",
            [],
            image_bytes=b"fake image",
            mime_type="image/jpeg",
            vision_client=VisionClientStub(),
        )

        self.assertEqual(result["mode"], "AI视觉识别")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["items"][0]["food_name"], "米饭")

    def test_falls_back_to_demo_recognition_when_vision_client_fails(self):
        class FailingVisionClient:
            def recognize(self, filename, image_bytes, mime_type):
                raise RuntimeError("api unavailable")

        items = recognize_meal_image(
            "rice.jpg",
            [],
            image_bytes=b"fake image",
            mime_type="image/jpeg",
            vision_client=FailingVisionClient(),
        )

        self.assertEqual(items[0]["food_name"], "米饭")
        self.assertEqual(items[0]["recognition_source"], "演示回退")
        self.assertIn("AI视觉识别未成功", items[0]["reason"])
        self.assertIn("api unavailable", items[0]["reason"])

    def test_detailed_result_exposes_fallback_reason(self):
        class FailingVisionClient:
            def recognize(self, filename, image_bytes, mime_type):
                raise RuntimeError("image input is not supported")

        result = recognize_meal_image_detailed(
            "rice.jpg",
            [],
            image_bytes=b"fake image",
            mime_type="image/jpeg",
            vision_client=FailingVisionClient(),
        )

        self.assertEqual(result["mode"], "演示回退")
        self.assertEqual(result["status"], "fallback")
        self.assertIn("image input is not supported", result["message"])


if __name__ == "__main__":
    unittest.main()
