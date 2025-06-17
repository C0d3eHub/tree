from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from treeapp import views_dashboard # Import views_dashboard directly

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Changed to django-admin to avoid conflict
    path('admin/', views_dashboard.admin_user_list, name='admin_user_list'),  # Directly map to the correct view
    path('', include('treeapp.urls')),
]

# Add media URL configuration
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
