from flask import render_template

from .admin import register_admin_routes
from .auth import register_auth_routes
from .student import register_student_routes


def register_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html")

    register_auth_routes(app)
    register_student_routes(app)
    register_admin_routes(app)
