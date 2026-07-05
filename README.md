# Campus Fitness and Diet Management System

## Project Overview

Campus Fitness and Diet Management System is a Flask-based web application for student fitness tracking, diet logging, body metric management, food library maintenance, image-assisted meal recording, and local health recommendation analysis.

The system is designed for a university course project and follows a clean Flask application structure with separated routes, models, utilities, templates, static assets, tests, and documentation.

## Features

- Student registration, login, logout, and profile management
- Administrator login and food library management
- Workout record CRUD workflows
- Diet record CRUD workflows
- Body metric tracking and weight trend visualization
- Workout plan management
- Image-assisted diet recording with visual API support and demo fallback mode
- Local machine-learning-style health analysis and intelligent recommendations
- SQLite database initialization with a default administrator account
- Automated route and recommendation tests

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- Jinja2 templates
- Bootstrap 5
- Pytest / unittest

## Project Structure

```text
fitness_system/
├── app/
│   ├── __init__.py
│   ├── admin.py
│   ├── auth.py
│   ├── food_image_recognizer.py
│   ├── forms.py
│   ├── ml_recommender.py
│   ├── models.py
│   ├── routes.py
│   ├── student.py
│   ├── utils.py
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
│       ├── admin/
│       └── student/
├── docs/
├── instance/
├── migrations/
├── screenshots/
├── tests/
├── app.py
├── config.py
├── init_db.py
├── run.py
├── requirements.txt
└── README.md
```

See [docs/project_structure.md](docs/project_structure.md) for a detailed explanation of every folder and request flow.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

Initialize the database:

```bash
python init_db.py
```

Start the application:

```bash
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

Backward-compatible startup is also available:

```bash
python app.py
```

Default administrator account:

```text
Username: admin
Password: 123456
```

## Optional Vision API Configuration

The image-assisted diet feature can call a vision model compatible with OpenAI-style chat completions image input.

Copy the example environment file:

```bash
cp .env.example .env
```

Then fill in:

```text
VISION_API_URL=
VISION_API_KEY=
VISION_MODEL=
```

If no visual API is configured, the system automatically falls back to demo recognition mode so the project can still run and be demonstrated.

## Testing

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests -q
```

The environment variable avoids unrelated globally installed pytest plugins from interfering with this small Flask project.

## Screenshots

Screenshots can be added later under the `screenshots/` folder.

Suggested screenshots:

- `screenshots/home.png`
- `screenshots/student-dashboard.png`
- `screenshots/diet-recognition.png`
- `screenshots/admin-food-library.png`
- `screenshots/recommendation.png`

## Future Improvements

- Add password hashing and stronger authentication
- Add role-based decorators for cleaner access control
- Add database migrations with Flask-Migrate
- Add pagination and search for record lists
- Improve image recognition with a production vision model
- Add more charts for training and nutrition trends
- Add deployment configuration for Docker or cloud hosting

## Development Workflow

This project is managed with Git and GitHub. New features are developed on separate branches, committed with clear messages, and merged into the main branch through pull requests.