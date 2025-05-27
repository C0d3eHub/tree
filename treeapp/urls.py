from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # HOMEPAGE shows index.html
    path('tree/', views.tree_view, name='tree_view'),  # move tree.html to /tree/     
    path('data/', views.tree_data, name='tree_data'),
    path('submit-correction/', views.submit_correction, name='submit_correction'),
    path('add-member/', views.add_member, name='add_member'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('help/', views.help_view, name='help'),
    path('add-children/', views.add_multiple_children, name='add_multiple_children'),
]
