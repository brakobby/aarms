# AARMS - Single App Structure

## Setup
1. Activate venv: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
2. Run migrations: `python manage.py makemigrations && python manage.py migrate`
3. Create superuser: `python manage.py createsuperuser`
4. Run server: `python manage.py runserver`

## Structure
- **aarms/** - Project settings
- **school/** - ONE app with everything (models, views, urls, templates)
- **static/** - CSS, JS, images
- **media/** - Uploaded files
- **templates/** - Global templates

Everything is simple and in one place!