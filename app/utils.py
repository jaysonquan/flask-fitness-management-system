import os
from pathlib import Path

from sqlalchemy import text

from .models import Admin, db


def load_local_env():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def initialize_database():
    db.create_all()
    ensure_workout_plan_user_id_column()
    seed_default_admin()


def ensure_workout_plan_user_id_column():
    rows = db.session.execute(text("PRAGMA table_info(workout_plans)")).fetchall()
    column_names = {row[1] for row in rows}
    if rows and "user_id" not in column_names:
        db.session.execute(text("ALTER TABLE workout_plans ADD COLUMN user_id INTEGER"))
        db.session.commit()


def seed_default_admin():
    admin = Admin.query.filter_by(username="admin").first()
    if admin:
        return

    db.session.add(Admin(username="admin", password="123456", admin_name="系统管理员"))
    db.session.commit()


def vision_config_notice():
    api_url = os.environ.get("VISION_API_URL", "")
    model = os.environ.get("VISION_MODEL", "")
    if "api.deepseek.com" in api_url:
        return (
            "当前配置的是 DeepSeek 文本接口。该接口返回过不支持 image_url 的错误，"
            "因此真实图片识别可能无法生效，系统会显示错误原因并回退到演示识别。"
            "若要准确识别餐食图片，请换成支持图片输入的视觉模型接口。"
        )
    if not api_url or not model or not os.environ.get("VISION_API_KEY"):
        return "尚未配置视觉 API，当前会使用演示回退识别。"
    return ""


def build_ai_recommendations(user):
    goal = user.goal_type or "保持体态"
    level = user.fitness_level or "新手"
    weekly_days = user.weekly_days or 3

    if goal == "减脂":
        training_focus = [
            "以有氧训练和全身力量训练结合为主",
            "优先安排中等强度持续运动，逐步增加训练时长",
            "每周保留 1 到 2 天恢复日，避免过度疲劳",
        ]
        diet_focus = [
            "控制总热量摄入，保证蛋白质来源稳定",
            "减少高糖饮料和油炸食物，增加蔬菜与全谷物",
            "训练后补充适量蛋白质，帮助维持肌肉量",
        ]
    elif goal == "增肌":
        training_focus = [
            "以复合力量动作为核心，关注渐进负荷",
            "每个大肌群每周安排 2 次左右刺激",
            "记录训练重量和次数，观察力量提升趋势",
        ]
        diet_focus = [
            "在日常消耗基础上适度增加热量摄入",
            "每餐安排优质蛋白质，搭配足量碳水",
            "训练前后注意补水，并保证睡眠恢复",
        ]
    else:
        training_focus = [
            "保持规律训练，力量、心肺和灵活性均衡安排",
            "根据课程和作息选择稳定可坚持的训练时间",
            "每 4 周回顾一次体重、围度和训练完成情况",
        ]
        diet_focus = [
            "维持三餐规律，避免长期空腹或暴食",
            "优先选择低加工食物，保证蛋白质和膳食纤维",
            "根据体重变化微调主食和脂肪摄入",
        ]

    return {
        "goal": goal,
        "level": level,
        "weekly_frequency": f"每周 {weekly_days} 次",
        "training_focus": training_focus,
        "diet_focus": diet_focus,
    }
