# BOSS - Business Operations Support System

Django web app for team leaders to manage administrative HR tasks and track initiatives/projects using agile methodologies.

## Project Structure

```
boss_core/       # Django project config (settings, urls, wsgi)
team/            # HR module: employees, absences, vacations, birthdays
initiatives/     # Initiatives module: quarters, sprints, user stories, tasks
templates/       # Global templates directory (base.html, home.html, partials/)
static/          # Static files (CSS, JS, images)
manage.py
requirements.txt
create_initial_data.py  # Seed script for dev data
```

## Tech Stack

- **Backend**: Django 5.2, Python
- **Frontend**: Tailwind CSS (recently migrated from Bootstrap 5.3), Font Awesome, HTMX (`django-htmx`)
- **Forms**: `django-crispy-forms` + `crispy-bootstrap5`
- **Database**: SQLite (`db.sqlite3`) — development only
- **Language/Locale**: Spanish (`es-mx`), timezone `America/Mexico_City`

## Common Commands

```bash
# Run dev server
python manage.py runserver

# Apply migrations
python manage.py migrate

# Create/apply new migration after model change
python manage.py makemigrations
python manage.py migrate

# Create initial seed data
python create_initial_data.py

# Django shell
python manage.py shell
```

## Key Apps & URLs

### team/
- `/team/` — Team dashboard
- `/team/employees/` — Employee list/detail/create/edit
- `/team/absences/` — Absence management
- `/team/vacations/` — Vacation control
- `/team/birthdays/` — Birthday calendar

### initiatives/
- `/initiatives/` — Initiatives dashboard
- `/initiatives/list/` — All initiatives
- `/initiatives/operational/` — Recurring operational tasks
- `/initiatives/sprint/` — Active sprint board (Kanban)
- `/initiatives/quarter/` — Active quarter summary

### Other
- `/admin/` — Django admin panel
- `/` — Home (redirects to login if unauthenticated)

## Data Models Overview

### team
- `Employee` — Linked 1:1 to Django `User`; has `full_name`, `age`, `years_of_service` properties
- `AbsenceType` — Absence categories with color codes
- `Absence` — Employee absence records with date ranges
- `Vacation` — Annual vacation day tracking per employee
- `Birthday` — Unmanaged model with class method for upcoming birthdays

### initiatives
- `Quarter` — Trimestral periods (Q1–Q4); only one can be `is_active=True`
- `InitiativeType` — Categories: OPERATIONAL, PROJECT, INITIATIVE, IMPROVEMENT, SUPPORT
- `Initiative` — Main entity; statuses: BACKLOG, PLANNED, IN_PROGRESS, BLOCKED, COMPLETED, CANCELLED
- `OperationalTask` — Recurring task details (frequency, schedule) for operational initiatives
- `Sprint` — Agile sprints linked to a Quarter; only one active at a time
- `UserStory` — Stories linked to an Initiative (epic); Fibonacci story points (1–21)
- `Task` — Sub-tasks within a UserStory; updates parent story/initiative progress on save
- `InitiativeUpdate` — Progress updates, blockers, risks, achievements
- `InitiativeMetric` — KPI tracking per initiative

## Architecture Notes

- Templates live in `/templates/` (project-level), not inside each app
- `base.html` is the global layout base; all other templates extend it
- HTMX is used for partial page updates; `django-htmx` middleware is active
- Only one `Quarter` and one `Sprint` can be active at a time (enforced in `save()`)
- `Task.save()` cascades progress updates up to `UserStory` → `Initiative`
- `LOGIN_URL = 'login'`, `LOGIN_REDIRECT_URL = 'home'`

## Development Notes

- Database is SQLite; `db.sqlite3` is gitignored (not committed)
- `DEBUG = True` in settings — do not use in production
- Secret key is hardcoded in settings — must be replaced before any production deploy
- Media files: `MEDIA_URL = 'media/'`, `MEDIA_ROOT = BASE_DIR / 'media'`

## Test Users (after running create_initial_data.py)

| Role          | Username   | Password    |
|---------------|------------|-------------|
| Admin         | admin      | admin123    |
| Employees     | jperez, mgarcia, clopez, amartinez | password123 |
