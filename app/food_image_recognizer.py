import base64
import json
import os
import re
import urllib.error
import urllib.request


DEMO_FOODS = {
    "rice": {
        "food_name": "米饭",
        "estimated_grams": 180,
        "calories_per_100g": 116,
        "confidence": "中",
        "reason": "演示样例中匹配到米饭",
    },
    "chicken": {
        "food_name": "鸡胸肉",
        "estimated_grams": 120,
        "calories_per_100g": 165,
        "confidence": "高",
        "reason": "演示样例中匹配到鸡胸肉",
    },
    "broccoli": {
        "food_name": "西兰花",
        "estimated_grams": 80,
        "calories_per_100g": 34,
        "confidence": "中",
        "reason": "演示样例中匹配到西兰花",
    },
    "egg": {
        "food_name": "鸡蛋",
        "estimated_grams": 55,
        "calories_per_100g": 144,
        "confidence": "高",
        "reason": "演示样例中匹配到鸡蛋",
    },
    "apple": {
        "food_name": "苹果",
        "estimated_grams": 180,
        "calories_per_100g": 53,
        "confidence": "中",
        "reason": "演示样例中匹配到苹果",
    },
    "oat": {
        "food_name": "燕麦",
        "estimated_grams": 60,
        "calories_per_100g": 380,
        "confidence": "中",
        "reason": "演示样例中匹配到燕麦",
    },
    "milk": {
        "food_name": "牛奶",
        "estimated_grams": 250,
        "calories_per_100g": 54,
        "confidence": "中",
        "reason": "演示样例中匹配到牛奶",
    },
}


FOOD_ALIASES = {
    "白米饭": "米饭",
    "米饭": "米饭",
    "米": "米饭",
    "鸡肉": "鸡胸肉",
    "鸡胸": "鸡胸肉",
    "鸡胸肉": "鸡胸肉",
    "西蓝花": "西兰花",
    "西兰花": "西兰花",
    "青花菜": "西兰花",
    "鸡蛋": "鸡蛋",
    "水煮蛋": "鸡蛋",
    "苹果": "苹果",
    "燕麦": "燕麦",
    "牛奶": "牛奶",
}


DEFAULT_MEAL = ["rice", "chicken", "broccoli"]


class OpenAIVisionMealClient:
    def __init__(self, api_url, api_key, model):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model

    @classmethod
    def from_env(cls):
        api_url = os.environ.get("VISION_API_URL", "").strip()
        api_key = os.environ.get("VISION_API_KEY", "").strip()
        model = os.environ.get("VISION_MODEL", "").strip()
        if not api_url or not api_key or not model:
            return None
        return cls(api_url, api_key, model)

    def recognize(self, filename, image_bytes, mime_type):
        data_url = _build_data_url(image_bytes, mime_type)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是餐食图片识别助手。只输出 JSON 数组，不要 Markdown。"
                        "每项包含 food_name, estimated_grams, confidence, reason。"
                        "estimated_grams 是根据图片估算的克数，confidence 只能是 高/中/低。"
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请识别这张餐食图片中大致包含哪些食物，并估算每种食物的克数。",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                    ],
                },
            ],
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"视觉 API HTTP {exc.code}：{error_body[:500]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"视觉 API 请求失败：{exc}") from exc

        return _parse_vision_response(response_body)


def recognize_meal_image(
    filename,
    food_library=None,
    image_bytes=None,
    mime_type=None,
    vision_client=None,
):
    return recognize_meal_image_detailed(
        filename,
        food_library,
        image_bytes=image_bytes,
        mime_type=mime_type,
        vision_client=vision_client,
    )["items"]


def recognize_meal_image_detailed(
    filename,
    food_library=None,
    image_bytes=None,
    mime_type=None,
    vision_client=None,
):
    calories_lookup = _build_calories_lookup(food_library or [])
    client = vision_client if vision_client is not None else OpenAIVisionMealClient.from_env()

    fallback_reason = ""
    if client and image_bytes:
        try:
            ai_items = client.recognize(filename, image_bytes, mime_type or "image/jpeg")
            normalized_items = _normalize_ai_items(ai_items, calories_lookup)
            if normalized_items:
                return {
                    "items": normalized_items,
                    "mode": "AI视觉识别",
                    "status": "success",
                    "message": "AI视觉识别成功，请确认克数后保存。",
                }
            fallback_reason = "AI 视觉接口未返回可用食物结果"
        except Exception as exc:
            fallback_reason = str(exc)
    elif not client:
        fallback_reason = "未配置可用的视觉 API"
    elif not image_bytes:
        fallback_reason = "未读取到图片内容"

    message = "AI视觉识别未成功，已使用演示回退。"
    if fallback_reason:
        message = f"{message}原因：{fallback_reason}"

    return {
        "items": _demo_items(filename, calories_lookup, fallback_reason),
        "mode": "演示回退",
        "status": "fallback",
        "message": message,
    }


def _demo_items(filename, calories_lookup, fallback_reason=""):
    matched_keys = _detect_demo_food_keys(filename)
    return [
        _build_item(DEMO_FOODS[key], calories_lookup, "演示回退", fallback_reason)
        for key in matched_keys
    ]


def _normalize_ai_items(ai_items, calories_lookup):
    normalized = []
    for raw_item in ai_items:
        raw_name = str(raw_item.get("food_name", "")).strip()
        if not raw_name:
            continue
        food_name = _match_food_name(raw_name, calories_lookup)
        grams = _safe_float(raw_item.get("estimated_grams"), 100.0)
        confidence = _normalize_confidence(raw_item.get("confidence"))
        reason = str(raw_item.get("reason", "AI 根据图片估算")).strip()
        calories = _lookup_calories(food_name, calories_lookup)

        normalized.append(
            {
                "food_name": food_name,
                "estimated_grams": round(grams, 1),
                "calories_per_100g": calories,
                "estimated_calories": round(grams * calories / 100, 1),
                "confidence": confidence,
                "source": "食物库" if food_name in calories_lookup else "系统默认估算",
                "recognition_source": "AI视觉识别",
                "reason": reason,
            }
        )
    return normalized


def _detect_demo_food_keys(filename):
    normalized = re.sub(r"[^a-z0-9]+", " ", (filename or "").lower())
    matched = [key for key in DEMO_FOODS if key in normalized]
    return matched or DEFAULT_MEAL


def _build_item(food_info, calories_lookup, recognition_source, fallback_reason=""):
    food_name = food_info["food_name"]
    calories = _lookup_calories(food_name, calories_lookup)
    grams = food_info["estimated_grams"]
    source = "食物库" if food_name in calories_lookup else "系统默认估算"
    reason = food_info["reason"]
    if fallback_reason:
        reason = f"AI视觉识别未成功，已回退：{fallback_reason}"

    return {
        "food_name": food_name,
        "estimated_grams": grams,
        "calories_per_100g": calories,
        "estimated_calories": round(grams * calories / 100, 1),
        "confidence": food_info["confidence"],
        "source": source,
        "recognition_source": recognition_source,
        "reason": reason,
    }


def _build_calories_lookup(food_library):
    lookup = {}
    for food in food_library:
        if food.food_name and food.calories is not None:
            lookup[food.food_name] = float(food.calories)
    return lookup


def _match_food_name(raw_name, calories_lookup):
    compact_name = re.sub(r"\s+", "", raw_name)
    alias = FOOD_ALIASES.get(compact_name)
    if alias:
        return alias
    if compact_name in calories_lookup:
        return compact_name
    for known_name in calories_lookup:
        if compact_name in known_name or known_name in compact_name:
            return known_name
    for alias_name, standard_name in FOOD_ALIASES.items():
        if alias_name in compact_name or compact_name in alias_name:
            return standard_name
    return raw_name


def _lookup_calories(food_name, calories_lookup):
    if food_name in calories_lookup:
        return calories_lookup[food_name]
    for demo_food in DEMO_FOODS.values():
        if demo_food["food_name"] == food_name:
            return float(demo_food["calories_per_100g"])
    return 100.0


def _normalize_confidence(value):
    value = str(value or "中").strip()
    return value if value in {"高", "中", "低"} else "中"


def _safe_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_data_url(image_bytes, mime_type):
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type or 'image/jpeg'};base64,{encoded}"


def _parse_vision_response(response_body):
    payload = json.loads(response_body)
    content = payload["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return _extract_json_array(content)


def _extract_json_array(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    if not text.startswith("["):
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            raise ValueError("视觉 API 未返回 JSON 数组")
        text = match.group(0)
    result = json.loads(text)
    if not isinstance(result, list):
        raise ValueError("视觉 API 返回结果不是数组")
    return result
