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

# Automatically create/reset default admin user
python manage.py shell -c "from django.contrib.auth.models import User; u, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'}); u.set_password('admin123'); u.is_superuser = True; u.is_staff = True; u.is_active = True; u.save(); print('>>> ADMIN READY: admin / admin123 <<<')"

