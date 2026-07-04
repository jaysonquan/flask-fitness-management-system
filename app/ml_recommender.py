from collections import defaultdict
from math import sqrt
from statistics import mean


FEATURE_RANGES = {
    "bmi": (16.0, 35.0),
    "weekly_days": (0.0, 7.0),
    "workout_count": (0.0, 12.0),
    "avg_daily_calories": (1000.0, 4000.0),
    "weight_delta": (-8.0, 8.0),
    "goal_code": (0.0, 1.0),
}


GOAL_CODES = {
    "减脂": 0.15,
    "保持体态": 0.5,
    "提升体能": 0.6,
    "增肌": 0.85,
}


PROTOTYPE_SAMPLES = [
    ("训练不足型", [24.0, 0.0, 0.0, 2100.0, 0.5, 0.5]),
    ("训练不足型", [26.0, 1.0, 1.0, 2300.0, 1.0, 0.15]),
    ("训练不足型", [22.0, 1.0, 0.0, 1900.0, -0.5, 0.6]),
    ("减脂优先型", [29.0, 3.0, 4.0, 2800.0, 2.0, 0.15]),
    ("减脂优先型", [31.0, 4.0, 5.0, 3000.0, 1.5, 0.15]),
    ("增肌优先型", [20.0, 4.0, 7.0, 2700.0, 0.0, 0.85]),
    ("增肌优先型", [21.5, 5.0, 8.0, 3000.0, 0.5, 0.85]),
    ("体重波动风险型", [24.0, 2.0, 3.0, 2500.0, 5.0, 0.5]),
    ("体重波动风险型", [25.0, 3.0, 4.0, 1700.0, -5.0, 0.15]),
    ("保持健康型", [22.0, 3.0, 6.0, 2100.0, 0.2, 0.5]),
    ("保持健康型", [23.0, 4.0, 8.0, 2300.0, -0.2, 0.6]),
]


PROFILE_RECOMMENDATIONS = {
    "训练不足型": "先把训练频率稳定到每周 2-3 次，再逐步增加强度。",
    "减脂优先型": "保持轻微热量缺口，搭配规律有氧和力量训练。",
    "增肌优先型": "围绕复合力量动作训练，并保证蛋白质和碳水摄入。",
    "体重波动风险型": "先稳定饮食、作息和记录习惯，再调整训练计划。",
    "保持健康型": "继续保持当前节奏，每 4 周复盘一次训练和饮食结构。",
}


def analyze_student_profile(user, body_records=None, workout_records=None, diet_records=None):
    body_records = sorted(body_records or [], key=lambda record: record.record_date)
    workout_records = workout_records or []
    diet_records = diet_records or []

    features = _extract_features(user, body_records, workout_records, diet_records)
    training_samples = _build_training_samples(features)
    profile = _classify_profile(features, training_samples)
    diet_risk = _analyze_diet_risk(features, diet_records)
    training_trend = _predict_training_trend(features, body_records, workout_records)
    suggestions = _build_suggestions(profile, diet_risk, training_trend)

    return {
        "algorithm": "本地可训练健康分析模型",
        "training_sample_count": len(training_samples),
        "feature_summary": _build_feature_summary(features),
        "profile": profile,
        "diet_risk": diet_risk,
        "training_trend": training_trend,
        "suggestions": suggestions,
        "profile_type": profile["label"],
        "confidence": profile["confidence"],
        "reasons": profile["reasons"],
        "recommendations": suggestions,
    }


def _extract_features(user, body_records, workout_records, diet_records):
    height = _number(getattr(user, "height", None), default=0.0)
    latest_weight = _latest_weight(user, body_records)
    bmi = _latest_bmi(user, body_records, height, latest_weight)
    weekly_days = _number(getattr(user, "weekly_days", None), default=0.0)
    workout_count = float(len(workout_records))
    avg_workout_duration = _average_field(workout_records, "duration_minutes", 0.0)
    avg_burned_calories = _average_field(workout_records, "calories_burned", 0.0)
    avg_daily_calories = _average_daily_calories(diet_records)
    diet_record_days = _diet_record_days(diet_records)
    meal_regularity = _meal_regularity(diet_records)
    weight_delta = _weight_delta(body_records)
    goal_code = GOAL_CODES.get(getattr(user, "goal_type", None), 0.5)

    return {
        "bmi": bmi,
        "weekly_days": weekly_days,
        "workout_count": workout_count,
        "avg_workout_duration": avg_workout_duration,
        "avg_burned_calories": avg_burned_calories,
        "avg_daily_calories": avg_daily_calories,
        "diet_record_days": diet_record_days,
        "meal_regularity": meal_regularity,
        "weight_delta": weight_delta,
        "goal_code": goal_code,
        "goal_type": getattr(user, "goal_type", "") or "保持体态",
    }


def _build_training_samples(features):
    samples = list(PROTOTYPE_SAMPLES)
    if features["workout_count"] > 0 or features["diet_record_days"] > 0:
        label = _rule_label_for_current_user(features)
        samples.append(
            (
                label,
                [
                    features["bmi"],
                    features["weekly_days"],
                    features["workout_count"],
                    features["avg_daily_calories"],
                    features["weight_delta"],
                    features["goal_code"],
                ],
            )
        )
    return samples


def _classify_profile(features, training_samples):
    centroids = _train_centroids(training_samples)
    current_vector = _scale_features(features)
    distances = sorted(
        (
            _euclidean_distance(current_vector, centroid),
            label,
        )
        for label, centroid in centroids.items()
    )
    nearest_distance, label = distances[0]
    second_distance = distances[1][0] if len(distances) > 1 else nearest_distance + 1.0
    confidence = round(
        max(0.0, min(100.0, (1 - nearest_distance / (second_distance + 0.001)) * 100)),
        1,
    )

    return {
        "label": label,
        "confidence": confidence,
        "reasons": _build_profile_reasons(features),
    }


def _train_centroids(training_samples):
    grouped = defaultdict(list)
    for label, values in training_samples:
        grouped[label].append(_scale_vector(values))
    return {label: _average_vectors(vectors) for label, vectors in grouped.items()}


def _rule_label_for_current_user(features):
    if features["weekly_days"] <= 1 or features["workout_count"] <= 1:
        return "训练不足型"
    if abs(features["weight_delta"]) >= 4:
        return "体重波动风险型"
    if features["goal_type"] == "增肌" or features["bmi"] < 18.5:
        return "增肌优先型"
    if features["goal_type"] == "减脂" or features["bmi"] >= 28:
        return "减脂优先型"
    return "保持健康型"


def _analyze_diet_risk(features, diet_records):
    labels = []
    reasons = []
    avg_calories = features["avg_daily_calories"]

    if not diet_records:
        labels.append("饮食记录不足")
        reasons.append("近期没有饮食记录，模型无法准确判断摄入结构。")
    if avg_calories >= 2800:
        labels.append("热量偏高")
        reasons.append(f"平均每日饮食热量约 {avg_calories:.0f} 千卡，明显偏高。")
    elif diet_records and avg_calories <= 1400:
        labels.append("热量偏低")
        reasons.append(f"平均每日饮食热量约 {avg_calories:.0f} 千卡，可能影响训练恢复。")
    if diet_records and features["meal_regularity"] < 0.6:
        labels.append("餐次记录不完整")
        reasons.append("早餐、午餐、晚餐记录不够完整，热量估算可能偏差较大。")
    if features["goal_type"] == "减脂" and avg_calories >= 2400:
        labels.append("与减脂目标不匹配")
        reasons.append("当前摄入水平不利于形成稳定、温和的热量缺口。")
    if features["goal_type"] == "增肌" and diet_records and avg_calories <= 1800:
        labels.append("与增肌目标不匹配")
        reasons.append("当前摄入可能不足以支持力量训练后的恢复和增长。")

    labels = _dedupe(labels)
    if not labels:
        labels.append("饮食结构较稳定")
        reasons.append("近期热量和餐次记录整体较平稳。")

    return {
        "level": _diet_risk_level(labels),
        "labels": labels,
        "reasons": reasons,
    }


def _predict_training_trend(features, body_records, workout_records):
    if len(body_records) < 2:
        return {
            "label": "数据不足，暂不预测",
            "confidence": 0.0,
            "reasons": ["至少需要两条身体指标记录，才能判断体重和训练趋势。"],
        }

    reasons = []
    weight_delta = features["weight_delta"]
    workout_count = features["workout_count"]
    avg_duration = features["avg_workout_duration"]
    avg_calories = features["avg_daily_calories"]

    if weight_delta <= -1.0 and workout_count >= 2:
        label = "体重可能下降"
        confidence = 76.0
        reasons.append(f"体重较首次记录下降 {abs(weight_delta):.1f} kg。")
        reasons.append(f"近期有 {int(workout_count)} 条训练记录，训练行为较稳定。")
    elif weight_delta >= 1.0 and avg_calories >= 2400:
        label = "体重可能上升"
        confidence = 72.0
        reasons.append(f"体重较首次记录上升 {weight_delta:.1f} kg。")
        reasons.append("当前平均饮食热量偏高，可能推动体重继续上升。")
    elif abs(weight_delta) < 1.0 and workout_count >= 2:
        label = "体重趋于稳定"
        confidence = 68.0
        reasons.append("近期体重变化小于 1 kg，整体趋势较平稳。")
    else:
        label = "训练效果不明显"
        confidence = 55.0
        reasons.append("当前体重、训练频率和饮食数据尚未形成明确趋势。")

    if workout_records and avg_duration < 25:
        confidence = max(40.0, confidence - 10)
        reasons.append("平均训练时长偏短，可能影响训练效果。")

    return {
        "label": label,
        "confidence": round(confidence, 1),
        "reasons": reasons,
    }


def _build_profile_reasons(features):
    reasons = []
    if features["weekly_days"] <= 2:
        reasons.append("每周训练天数偏低")
    if features["workout_count"] <= 1:
        reasons.append("近期训练记录较少")
    if features["bmi"] >= 28:
        reasons.append("BMI 偏高，适合优先关注减脂和心肺能力")
    elif features["bmi"] < 18.5:
        reasons.append("BMI 偏低，适合关注增肌和营养补充")
    if features["avg_daily_calories"] >= 2600:
        reasons.append("平均饮食热量偏高")
    if abs(features["weight_delta"]) >= 4:
        reasons.append("体重变化幅度较大")
    if not reasons:
        reasons.append("身体数据、饮食数据和训练数据整体较平稳")
    return reasons


def _build_suggestions(profile, diet_risk, training_trend):
    suggestions = [PROFILE_RECOMMENDATIONS[profile["label"]]]
    if "热量偏高" in diet_risk["labels"]:
        suggestions.append("优先减少高热量零食和含糖饮料，保持每餐主食、蛋白、蔬菜搭配。")
    if "热量偏低" in diet_risk["labels"]:
        suggestions.append("增加优质蛋白和主食，避免因摄入过低影响训练恢复。")
    if "饮食记录不足" in diet_risk["labels"]:
        suggestions.append("连续记录 3-7 天饮食，模型分析会更稳定。")
    if training_trend["label"] == "数据不足，暂不预测":
        suggestions.append("至少补充两次身体指标记录，便于判断体重趋势。")
    elif training_trend["label"] == "训练效果不明显":
        suggestions.append("保持固定训练周期，并记录训练时长和消耗热量。")
    else:
        suggestions.append(f"当前趋势为“{training_trend['label']}”，建议每周复盘一次。")
    return _dedupe(suggestions)


def _build_feature_summary(features):
    return {
        "BMI": f"{features['bmi']:.1f}",
        "每周计划训练": f"{int(features['weekly_days'])} 天",
        "训练记录数": f"{int(features['workout_count'])} 条",
        "平均训练时长": f"{features['avg_workout_duration']:.0f} 分钟",
        "平均运动消耗": f"{features['avg_burned_calories']:.0f} 千卡",
        "平均每日热量": f"{features['avg_daily_calories']:.0f} 千卡",
        "饮食记录天数": f"{int(features['diet_record_days'])} 天",
        "餐次完整度": f"{features['meal_regularity'] * 100:.0f}%",
        "体重变化": f"{features['weight_delta']:+.1f} kg",
    }


def _scale_vector(values):
    return [
        _scale_value("bmi", values[0]),
        _scale_value("weekly_days", values[1]),
        _scale_value("workout_count", values[2]),
        _scale_value("avg_daily_calories", values[3]),
        _scale_value("weight_delta", values[4]),
        _scale_value("goal_code", values[5]),
    ]


def _scale_features(features):
    return [
        _scale_value("bmi", features["bmi"]),
        _scale_value("weekly_days", features["weekly_days"]),
        _scale_value("workout_count", features["workout_count"]),
        _scale_value("avg_daily_calories", features["avg_daily_calories"]),
        _scale_value("weight_delta", features["weight_delta"]),
        _scale_value("goal_code", features["goal_code"]),
    ]


def _scale_value(name, value):
    low, high = FEATURE_RANGES[name]
    clamped = min(max(float(value), low), high)
    return (clamped - low) / (high - low)


def _latest_bmi(user, body_records, height, weight):
    for record in reversed(body_records):
        bmi = _number(getattr(record, "bmi", None), default=None)
        if bmi:
            return bmi
    if height and weight:
        height_meters = height / 100
        return weight / (height_meters * height_meters)
    return _number(getattr(user, "bmi", None), default=22.0)


def _latest_weight(user, body_records):
    for record in reversed(body_records):
        weight = _number(getattr(record, "weight", None), default=None)
        if weight:
            return weight
    return _number(getattr(user, "weight", None), default=65.0)


def _weight_delta(body_records):
    if len(body_records) >= 2:
        first = _number(getattr(body_records[0], "weight", None), default=None)
        last = _number(getattr(body_records[-1], "weight", None), default=None)
        if first is not None and last is not None:
            return last - first
    return 0.0


def _average_field(records, field_name, default):
    values = [
        _number(getattr(record, field_name, None), default=None)
        for record in records
    ]
    values = [value for value in values if value is not None]
    return mean(values) if values else default


def _average_daily_calories(diet_records):
    daily_totals = defaultdict(float)
    for record in diet_records:
        calories = _number(getattr(record, "total_calories", None), default=None)
        record_date = getattr(record, "record_date", None)
        if calories is not None and record_date is not None:
            daily_totals[record_date] += calories
    return mean(daily_totals.values()) if daily_totals else 2100.0


def _diet_record_days(diet_records):
    return float(
        len(
            {
                getattr(record, "record_date", None)
                for record in diet_records
                if getattr(record, "record_date", None)
            }
        )
    )


def _meal_regularity(diet_records):
    if not diet_records:
        return 0.0
    meals_by_day = defaultdict(set)
    for record in diet_records:
        record_date = getattr(record, "record_date", None)
        meal_type = getattr(record, "meal_type", None)
        if record_date and meal_type:
            meals_by_day[record_date].add(meal_type)
    if not meals_by_day:
        return 0.0
    regularity_scores = [min(len(meals) / 3.0, 1.0) for meals in meals_by_day.values()]
    return mean(regularity_scores)


def _diet_risk_level(labels):
    if any(
        label in labels
        for label in {"热量偏高", "热量偏低", "与减脂目标不匹配", "与增肌目标不匹配"}
    ):
        return "高风险"
    if any(label in labels for label in {"饮食记录不足", "餐次记录不完整"}):
        return "中风险"
    return "低风险"


def _average_vectors(vectors):
    return [
        sum(vector[index] for vector in vectors) / len(vectors)
        for index in range(len(vectors[0]))
    ]


def _euclidean_distance(left, right):
    return sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def _dedupe(items):
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def _number(value, default=0.0):
    if value is None or value == "":
        return default
    return float(value)
