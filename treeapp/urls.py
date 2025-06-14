from django.urls import path
from . import views, admin_views, views_email, views_register, views_blood, views_album, views_post, views_dashboard, views_profile
from django.conf import settings
from django.conf.urls.static import static
from .views_blood import toggle_hide_donor
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('tree/', views.tree_view, name='tree'),
    path('api/tree/', views.tree_data, name='tree_data'),
    path('data/', views.tree_data, name='tree_data_legacy'),  # Add this line for compatibility
    path('submit-correction/', views.submit_correction, name='submit_correction'),
    path('add-member/', views.add_member, name='add_member'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('help/', views.help_view, name='help'),
    path('add-multiple-children/', views.add_multiple_children, name='add_multiple_children'),
    path('instructions/', views.instructions_view, name='instructions'),
    path('posts/', views.posts_view, name='posts'),
    
    # Dashboard
    path('dashboard/', views_dashboard.user_dashboard, name='user_dashboard'),
    path('update-profile/', views_dashboard.update_profile, name='update_profile'),
    path('verify-email/', views_dashboard.verify_email, name='verify_email'),
    
    # User Profile
    path('profile/', views_profile.user_profile, name='user_profile'),
    path('profile/<str:tab>/', views_profile.user_profile, name='user_profile_tab'),
    
    # Album and Post URLs
    path('add-album/', views_dashboard.create_album, name='add_album'),
    path('view-album/<int:album_id>/', views_dashboard.view_album, name='view_album'),
    path('edit-album/<int:album_id>/', views_dashboard.edit_album, name='edit_album'),
    
    path('add-post/', views_dashboard.add_post, name='add_post'),
    path('view-post/<int:post_id>/', views_dashboard.view_post, name='view_post'),
    path('edit-post/<int:post_id>/', views_dashboard.edit_post, name='edit_post'),
    
    # Legacy album and post URLs
    path('add-photo/<int:album_id>/', views_album.add_photo, name='add_photo'),
    path('my-albums/', views_album.my_albums, name='my_albums'),
    path('my-posts/', views_post.my_posts, name='my_posts'),
    
    # Authentication URLs
    path('register/', views_register.register_view, name='register'),
    path('verify-register-otp/', views_register.verify_register_otp, name='verify_register_otp'),
    path('resend-register-otp/', views_register.resend_register_otp, name='resend_register_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Email verification
    path('verify-email/<str:token>/', views_email.verify_email, name='verify_email'),
    path('resend-verification/', views_email.resend_verification, name='resend_verification'),
    
    # Password reset
    path('password-reset/', views_email.password_reset_view, name='password_reset'),
    path('send-otp/', views_email.send_otp, name='send_otp'),
    path('verify-otp/', views_email.verify_otp, name='verify_otp'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='treeapp/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='treeapp/password_reset_complete.html'),
         name='password_reset_complete'),
    
    # User tree
    path('my-tree/', views.my_family_tree, name='my_family_tree'),
    path('edit-member/<int:member_id>/', views.edit_member, name='edit_member'),
    path('upload-tree-image/', views.upload_tree_image, name='upload_tree_image'),
    
    # Admin views
    path('admin-users/', admin_views.admin_user_list, name='admin_user_list'),
    path('activate-user/<int:user_id>/', admin_views.activate_user, name='activate_user'),
    path('deactivate-user/<int:user_id>/', admin_views.deactivate_user, name='deactivate_user'),
    path('set-password/<int:user_id>/', admin_views.set_password, name='set_password'),
    path('admin-dashboard/', admin_views.admin_content_dashboard, name='admin_content_dashboard'),
    path('approve-album/<int:album_id>/', admin_views.approve_album, name='approve_album'),
    path('reject-album/<int:album_id>/', admin_views.reject_album, name='reject_album'),
    path('approve-post/<int:post_id>/', admin_views.approve_post, name='approve_post'),
    path('reject-post/<int:post_id>/', admin_views.reject_post, name='reject_post'),
    path('unpublish-album/<int:album_id>/', admin_views.unpublish_album, name='unpublish_album'),
    path('unpublish-post/<int:post_id>/', admin_views.unpublish_post, name='unpublish_post'),
    
    # Blood Bank views
    path('blood-bank/', views_blood.blood_bank_view, name='blood_bank'),
    path('blood-donor/', views_blood.blood_donor_view, name='blood_donor'),
    path('blood-request/', views_blood.blood_request_view, name='blood_request'),
    path('verify-otp-custom/', views_blood.verify_otp_custom, name='verify_otp_custom'),
    path('admin-blood-dashboard/', admin_views.admin_blood_dashboard, name='admin_blood_dashboard'),
    path('toggle-hide-donor/<int:user_id>/', toggle_hide_donor, name='toggle_hide_donor'),
    
    # New calendar page URL
    path('calendar/', views_dashboard.calendar_page, name='calendar_page'),
    path('donate/', views_dashboard.donation_page, name='donation_page'),
    path('record-donation/', views_dashboard.record_donation, name='record_donation'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)