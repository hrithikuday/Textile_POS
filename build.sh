#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
elif [ -f "../requirements.txt" ]; then
    pip install -r ../requirements.txt
fi

if [ -d "django_pos" ]; then
    cd django_pos
fi

python manage.py collectstatic --no-input
python manage.py migrate

# Create admin only if no superuser exists yet
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(is_superuser=True).exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"

