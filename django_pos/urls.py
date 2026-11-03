
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse


def init_admin_view(request):
    from django.contrib.auth.models import User
    u, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'})
    u.set_password('admin123')
    u.is_superuser = True
    u.is_staff = True
    u.is_active = True
    u.save()
    return HttpResponse("<h2>Admin user created successfully!</h2><p>Username: <b>admin</b><br>Password: <b>admin123</b></p><p><a href='/accounts/login/'>Click here to Log In</a></p>")


urlpatterns = [
    path('setup-admin/', init_admin_view),
    path('admin/', admin.site.urls),
    # Authentication: Login and Logout
    path('', include('authentication.urls')),
    # Index
    path('', include('pos.urls')),
    # Products
    path('products/', include('products.urls')),
    # Customers
    path('customers/', include('customers.urls')),
    # Sales
    path('sales/', include('sales.urls')),
    path('manage/', include('operations.urls')),
]
