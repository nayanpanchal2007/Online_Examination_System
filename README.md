# Student Online Examination System

A small Python for Data Science project for taking multiple-choice assessments, recording results, and exploring class performance. The app uses Streamlit for its browser interface, SQLite for persistent storage, and pandas for result analysis.

## Run the project

Use Python 3.10 or newer. From this folder, create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints the local URL to open in your browser, usually `http://localhost:8501`.

## Demo accounts

| Role | Username | Password |
| --- | --- | --- |
| Student | `alice` | `alice123` |
| Student | `sam` | `sam123` |
| Instructor | `admin` | `admin123` |

The first app launch creates `exam_portal.db` and loads two sample assessments. Student submissions are saved locally. The instructor can create assessments, add four-option questions, view submissions, compare average scores by subject, and inspect the score distribution.

## Project files

- `app.py`: Streamlit interface for sign-in, taking exams, results, and instructor tools.
- `database.py`: SQLite schema, demo data, authentication, exam management, and scoring functions.
- `tests/test_database.py`: focused tests for authentication, scoring, and exam creation.
- `requirements.txt`: Python dependencies.

This is a local classroom demonstration, not a production examination service. The demo credentials are public, and the app does not implement timed exams, account registration, or remote hosting.

## Run tests

```powershell
python -m unittest discover -s tests -v
```