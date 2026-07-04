from app import create_app, initialize_database


def init_database():
    app = create_app({"TESTING": True})
    with app.app_context():
        initialize_database()
        print("数据库初始化完成。")


if __name__ == "__main__":
    init_database()
