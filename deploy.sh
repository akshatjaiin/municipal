#!/bin/bash
# Railway deployment script
# This runs after the app is deployed

echo "Running post-deployment setup..."

# Run migrations
python manage.py migrate

# Create superuser if it doesn't exist
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@municipal.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Collect static files
python manage.py collectstatic --noinput

echo "Deployment setup complete!"