# Municipal (Django) Project

A Django project for managing civic complaints and workflows. It includes a `civic_saathi` app with REST APIs, admin, and demo data loader.

## Railway Deployment

### 1. Prerequisites
- Railway account
- Git repository

### 2. Deploy to Railway
1. Connect your GitHub repository to Railway
2. Railway will auto-detect the Django app
3. Set environment variables in Railway dashboard:
   ```
   DEBUG=False
   SECRET_KEY=your-super-secret-key-here
   ALLOWED_HOSTS=*
   ```
4. Railway will provide database credentials automatically

### 3. Post-Deployment Setup
The `deploy.sh` script will:
- Run migrations
- Create a superuser (admin/admin123)
- Collect static files

### 4. Access Admin Panel
- URL: `https://your-app-name.railway.app/admin/`
- Username: `admin`
- Password: `admin123`

**⚠️ Change the default password immediately!**

## Quick Start

### 1) Prerequisites
- Python 3.10+
- Windows PowerShell 5.1 (default shell)

### 2) Create virtual environment Ignore this
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) Install dependencies
```powershell
pip install -r requirements.txt
```

### 4) Apply migrations
```powershell
python manage.py makemigrations
python manage.py migrate
```

### 5) (Optional) Load demo data Ignore already pushed with db
```powershell
python load_demo_data.py
```

### 6) Run the development server
```powershell
python manage.py runserver
```

Open http://127.0.0.1:8000/admin in your browser.
username *test*
password *test*

## Project Structure

- `manage.py`: Django management utility
- `municipal/`: Project settings and URLs
- `civic_saathi/`: Main app (models, views, serializers, admin, migrations)
- `db.sqlite3`: Local development database (ignored in VCS)
- `load_demo_data.py`: Script to populate sample data

## Useful Commands

- Create superuser:
```powershell
python manage.py createsuperuser
```

- Run tests:
```powershell
python manage.py test
```

## Environment Variables

Configure secrets and environment-specific settings via environment variables when needed. For local development, defaults in `municipal/settings.py` should work out of the box.

## API

The project exposes REST endpoints from `civic_saathi`. See `civic_saathi/urls.py` and `civic_saathi/views.py` for available routes.

## Deployment Notes

- Use environment variables for `SECRET_KEY`, `DEBUG`, and database credentials.
- Collect static files in production:
```powershell
python manage.py collectstatic
```
- Use a production-ready WSGI/ASGI server (e.g., `gunicorn` for Linux) and a reverse proxy.

## License

Internal project. Do not distribute without permission.
