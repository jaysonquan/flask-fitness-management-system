# Project Structure

This document explains the production-style layout of the Flask Fitness Management System and how requests move through the application.

## Folder Overview

```text
app/
```

Main Flask application package. It contains the application factory, database models, route registration modules, business helpers, templates, and static assets.

```text
app/templates/
```

Jinja2 templates used by Flask. Shared layout files stay at the root level, while role-specific pages are grouped under `student/` and `admin/`.

```text
app/static/
```

Static frontend assets. CSS is placed under `app/static/css/`; JavaScript and images have their own folders for future expansion.

```text
instance/
```

Local runtime data such as the SQLite database. Database files are ignored by Git through `.gitignore`.

```text
migrations/
```

Reserved for future database migration files.

```text
tests/
```

Automated tests for routes, image recognition fallback behavior, and local recommendation analysis.

```text
docs/
```

Project documentation, including this structure document and the visual API integration guide.

```text
screenshots/
```

Reserved for screenshots that can be added to the README later.

## Python Files

```text
app/__init__.py
```

Defines `create_app()`, loads configuration, initializes SQLAlchemy, registers routes, and creates database tables when the app is not running in test mode.

```text
app/models.py
```

Contains SQLAlchemy models: `User`, `Admin`, `WorkoutPlan`, `Food`, `WorkoutRecord`, `DietRecord`, and `BodyRecord`.

```text
app/routes.py
```

Registers top-level routes and delegates role-specific route registration to `auth.py`, `student.py`, and `admin.py`.

```text
app/auth.py
```

Handles student registration, student login, administrator login, logout, session checks, and current student lookup.

```text
app/student.py
```

Contains all student-facing workflows: dashboard, profile, workout records, diet records, image-assisted diet recording, body records, charts, recommendations, and workout plans.

```text
app/admin.py
```

Contains administrator workflows: dashboard, food library list, add food, and delete food.

```text
app/forms.py
```

Provides small parsing helpers for dates, integers, and floats from HTML form submissions.

```text
app/utils.py
```

Provides environment loading, database initialization helpers, default administrator seeding, vision API notices, and recommendation text generation.

```text
app/food_image_recognizer.py
```

Implements image-assisted meal recognition, visual API parsing, food library matching, and demo fallback recognition.

```text
app/ml_recommender.py
```

Implements local health analysis logic used by the intelligent recommendation page.

```text
config.py
```

Stores application configuration classes such as `Config` and `TestingConfig`.

```text
run.py
```

Production-style local entry point for running the Flask app.

```text
app.py
```

Backward-compatible entry point so older commands such as `python app.py` still work.

```text
init_db.py
```

Initializes the database manually.

```text
models.py`, `food_image_recognizer.py`, `ml_recommender.py`
```

Thin compatibility wrappers that re-export the new package modules for old imports and tests.

## Request Flow

1. A user opens a URL in the browser.
2. Flask receives the request through the application created by `create_app()`.
3. `app/routes.py` has already registered all route handlers.
4. Authentication routes are handled in `app/auth.py`.
5. Student pages are handled in `app/student.py`.
6. Administrator pages are handled in `app/admin.py`.
7. Route handlers read form data, validate it with helpers from `app/forms.py`, and query or update models from `app/models.py`.
8. SQLAlchemy persists data to the SQLite database under `instance/`.
9. The route renders a Jinja2 template from `app/templates/`.
10. Static assets are served from `app/static/`.

## Template Organization

```text
app/templates/base.html
```

Shared layout, navigation, Bootstrap import, flash messages, and page content block.

```text
app/templates/index.html
```

Home page.

```text
app/templates/login.html
app/templates/register.html
```

Student login and registration pages.

```text
app/templates/student/
```

Student dashboard, profile, training, diet, body metrics, chart, workout plan, image recognition, and recommendation pages.

```text
app/templates/admin/
```

Administrator login, dashboard, and food library management pages.
