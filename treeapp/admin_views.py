from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count
from .models import BloodRequest, UserProfile, Album, Post
from django.contrib.admin.views.decorators import staff_member_required

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_user_list(request):
    users = User.objects.all().order_by('-date_joined')
    
    # Create a list of user data with profile information
    user_data = []
    for user in users:
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'name': '',
            'father_name': '',
            'phone': '',
            'plain_password': '',
            'email_verified': False
        }
        
        # Get profile data if it exists
        try:
            profile = UserProfile.objects.get(user=user)
            user_info['name'] = profile.name or ''
            user_info['father_name'] = profile.father_name or ''
            user_info['phone'] = profile.phone or ''
            user_info['plain_password'] = profile.plain_password or ''
            user_info['email_verified'] = profile.email_verified
        except UserProfile.DoesNotExist:
            pass
        
        user_data.append(user_info)
    
    # Get content statistics for the dashboard
    total_posts = Post.objects.count()
    total_albums = Album.objects.count()
    pending_posts_count = Post.objects.filter(is_approved=False).count()
    pending_albums_count = Album.objects.filter(is_approved=False).count()
    
    context = {
        'user_data': user_data,
        'total_posts': total_posts,
        'total_albums': total_albums,
        'pending_posts_count': pending_posts_count,
        'pending_albums_count': pending_albums_count,
    }
    
    return render(request, 'treeapp/admin_user_list.html', context)

@user_passes_test(is_admin)
def activate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request, f"User {user.username} has been activated.")
    return redirect('admin_user_list')

@user_passes_test(is_admin)
def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    messages.success(request, f"User {user.username} has been deactivated.")
    return redirect('admin_user_list')

@user_passes_test(is_admin)
def set_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        password = request.POST.get('password')
        if password:
            user.set_password(password)
            user.save()
            
            # Also update plain_password in UserProfile if it exists
            try:
                profile = user.userprofile
                profile.plain_password = password
                profile.save()
            except UserProfile.DoesNotExist:
                pass
                
            messages.success(request, f"Password for {user.username} has been updated.")
            return redirect('admin_user_list')
        else:
            messages.error(request, "Password cannot be empty.")
    
    return render(request, 'treeapp/set_password.html', {'user': user})

@user_passes_test(is_admin)
def admin_blood_dashboard(request):
    """Admin dashboard for blood bank statistics"""
    # Get all blood requests
    blood_requests = BloodRequest.objects.all().order_by('-created_at')
    
    # Split into donations and needs
    donations = blood_requests.filter(request_type='donate')
    needs = blood_requests.filter(request_type='need')
    
    # Get registered donors (not hidden)
    registered_donors = UserProfile.objects.filter(is_blood_donor=True, hide_from_donor_list=False)
    
    # Get blood group statistics (registered donors + donations)
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    blood_stats = {}
    for group in blood_groups:
        donors_count = donations.filter(blood_group=group).count() + registered_donors.filter(blood_group=group).count()
        needs_count = needs.filter(blood_group=group).count()
        blood_stats[group] = {
            'donors': donors_count,
            'needs': needs_count
        }
    
    # Get recent requests
    recent_requests = blood_requests[:10]
    
    # Add status for each donation and need
    donation_status = []
    for d in donations:
        status = 'Accepted' if d.is_registered_user else 'Pending'
        donation_status.append({'obj': d, 'status': status})
    need_status = []
    for n in needs:
        status = 'Accepted' if n.is_registered_user else 'Pending'
        need_status.append({'obj': n, 'status': status})
    
    context = {
        'blood_stats': blood_stats,
        'total_donors': len(donation_status) + registered_donors.count(),
        'total_needs': len(need_status),
        'recent_requests': blood_requests[:10],
        'donation_status': donation_status,
        'need_status': need_status,
    }
    
    return render(request, 'treeapp/admin/blood_dashboard.html', context)

@user_passes_test(is_admin)
def admin_content_dashboard(request):
    """Admin dashboard for user-generated content"""
    # Determine active tab
    active_tab = request.GET.get('tab', 'posts')
    if active_tab not in ['posts', 'albums']:
        active_tab = 'posts'
    
    # Get pending albums and posts
    pending_albums = Album.objects.filter(is_approved=False).order_by('-created_at')
    pending_posts = Post.objects.filter(is_approved=False).order_by('-created_at')
    
    # Get recent approved content
    recent_albums = Album.objects.filter(is_approved=True).order_by('-created_at')[:5]
    recent_posts = Post.objects.filter(is_approved=True).order_by('-created_at')[:5]
    
    # Get statistics
    total_albums = Album.objects.count()
    total_posts = Post.objects.count()
    pending_albums_count = pending_albums.count()
    pending_posts_count = pending_posts.count()
    
    # Get top contributors
    top_album_contributors = User.objects.annotate(
        album_count=Count('album')
    ).filter(album_count__gt=0).order_by('-album_count')[:5]
    
    top_post_contributors = User.objects.annotate(
        post_count=Count('post')
    ).filter(post_count__gt=0).order_by('-post_count')[:5]
    
    context = {
        'active_tab': active_tab,
        'pending_albums': pending_albums,
        'pending_posts': pending_posts,
        'recent_albums': recent_albums,
        'recent_posts': recent_posts,
        'total_albums': total_albums,
        'total_posts': total_posts,
        'pending_albums_count': pending_albums_count,
        'pending_posts_count': pending_posts_count,
        'top_album_contributors': top_album_contributors,
        'top_post_contributors': top_post_contributors,
    }
    
    return render(request, 'treeapp/admin/content_dashboard.html', context)

@user_passes_test(is_admin)
def approve_album(request, album_id):
    album = get_object_or_404(Album, id=album_id)
    album.is_approved = True
    album.save()
    messages.success(request, f"Album '{album.title}' has been approved.")
    return redirect('admin_content_dashboard')

@user_passes_test(is_admin)
def reject_album(request, album_id):
    album = get_object_or_404(Album, id=album_id)
    album.delete()
    messages.success(request, "Album has been rejected and deleted.")
    return redirect('admin_content_dashboard')

@user_passes_test(is_admin)
def approve_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_approved = True
    post.save()
    messages.success(request, f"Post '{post.title}' has been approved.")
    return redirect('admin_content_dashboard')

@user_passes_test(is_admin)
def reject_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    messages.success(request, "Post has been rejected and deleted.")
    return redirect('admin_content_dashboard')

@staff_member_required
def unpublish_album(request, album_id):
    album = get_object_or_404(Album, id=album_id)
    album.is_approved = False
    album.save()
    return redirect('admin_content_dashboard')

@staff_member_required
def unpublish_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_approved = False
    post.save()
    return redirect('admin_content_dashboard')