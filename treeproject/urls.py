from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def admin_redirect(request):
    return redirect('admin_user_list')

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Changed to django-admin to avoid conflict
    path('admin/', admin_redirect, name='admin'),  # Redirect /admin to admin_user_list
    path('', include('treeapp.urls')),
]

# Add media URL configuration
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
