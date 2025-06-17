from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import FamilyMember, UserProfile, Post, Album, AlbumPhoto, CustomNotification, Donation, UserLoginInfo
import json
from datetime import datetime
import random
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@login_required
def user_dashboard(request):
    """
    Main dashboard view that shows the user's tree, posts, and albums in tabs
    """
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    # Get family members
    family_members = UserProfile.objects.filter(family_root=user_profile.family_root).exclude(user=user)
    
    # Get today's date
    today = timezone.now().date()
    
    # Get birthday members
    birthday_members = UserProfile.objects.filter(
        date_of_birth__month=today.month,
        date_of_birth__day=today.day
    ).exclude(user=user)
    
    # Get anniversary members (only for married users)
    anniversary_members = UserProfile.objects.filter(
        marital_status='married',
        anniversary_date__month=today.month,
        anniversary_date__day=today.day
    ).exclude(user=user)
    
    # Get custom notifications (excluding suspension notifications)
    custom_notifications = CustomNotification.objects.filter(
        is_active=True
    ).exclude(
        message__icontains='suspended'
    ).order_by('-created_at')
    
    # Get calendar events
    calendar_events = []
    
    # Add birthday events
    for member in UserProfile.objects.filter(family_root=user_profile.family_root):
        if member.date_of_birth:
            # Create events for current year and next 5 years
            for year in range(today.year, today.year + 6):
                event_date = member.date_of_birth.replace(year=year)
                if event_date >= today:
                    calendar_events.append({
                        'type': 'birthday',
                        'title': f"{member.name}'s Birthday",
                        'start': event_date.isoformat(),
                        'backgroundColor': '#4CAF50',
                        'borderColor': '#4CAF50'
                    })
    
    # Add anniversary events
    for member in UserProfile.objects.filter(family_root=user_profile.family_root, marital_status='married'):
        if member.anniversary_date:
            # Create events for current year and next 5 years
            for year in range(today.year, today.year + 6):
                event_date = member.anniversary_date.replace(year=year)
                if event_date >= today:
                    calendar_events.append({
                        'type': 'anniversary',
                        'title': f"{member.name}'s Anniversary",
                        'start': event_date.isoformat(),
                        'backgroundColor': '#ff7e5f',
                        'borderColor': '#feb47b'
                    })
    
    context = {
        'user_profile': user_profile,
        'family_members': family_members,
        'birthday_members': birthday_members,
        'anniversary_members': anniversary_members,
        'custom_notifications': custom_notifications,
        'calendar_events': calendar_events,
    }
    
    return render(request, 'treeapp/user_dashboard.html', context)

@login_required
def add_post(request, user_id=None):
    """View for creating a new post"""
    # Determine the target user
    target_user = request.user
    if user_id and request.user.is_superuser:
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            target_user = request.user
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category = request.POST.get('category')
        image = request.FILES.get('image')
        if title and content and category:
            post = Post.objects.create(
                title=title,
                content=content,
                category=category,
                user=target_user,
                is_approved=False,
                image=image
            )
            return redirect('view_post', post_id=post.id)
    return render(request, 'treeapp/posts/create_post.html')

def view_post(request, post_id):
    """View for displaying a single post"""
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user can view this post
    if not post.is_approved and not request.user.is_authenticated:
        return redirect('login')
    
    if not post.is_approved and post.user != request.user and not request.user.is_staff:
        return redirect('user_dashboard')
    
    # Check if the user is the owner or a superuser to show edit option
    can_edit = request.user.is_authenticated and (post.user == request.user or request.user.is_superuser)
    
    return render(request, 'treeapp/posts/view_post.html', {
        'post': post,
        'can_edit': can_edit
    })

@login_required
def edit_post(request, post_id):
    """View for editing an existing post"""
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user can edit this post
    if post.user != request.user and not request.user.is_staff:
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category = request.POST.get('category')
        
        if title and content and category:
            post.title = title
            post.content = content
            post.category = category
            post.is_approved = False  # Reset approval status on edit
            post.save()
            return redirect('view_post', post_id=post.id)
    
    return render(request, 'treeapp/posts/edit_post.html', {'post': post})

@login_required
def create_album(request, user_id=None):
    """View for creating a new album"""
    # Determine the target user
    target_user = request.user
    if user_id and request.user.is_superuser:
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            target_user = request.user
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        photos = request.FILES.getlist('photos')
        if title:
            album = Album.objects.create(
                title=title,
                description=description,
                user=target_user,
                is_approved=False
            )
            for photo in photos:
                AlbumPhoto.objects.create(
                    album=album,
                    image=photo,
                    caption=''
                )
            return redirect('view_album', album_id=album.id)
    return render(request, 'treeapp/albums/create_album.html')

def view_album(request, album_id):
    """View for displaying a single album with photos"""
    album = get_object_or_404(Album, id=album_id)
    
    # Check if user can view this album
    if not album.is_approved and not request.user.is_authenticated:
        return redirect('login')
    
    if not album.is_approved and request.user.is_authenticated and album.user != request.user and not request.user.is_staff:
        return redirect('user_dashboard')
    
    # Check if the user is the owner or a superuser to show edit option
    can_edit = request.user.is_authenticated and (album.user == request.user or request.user.is_superuser)
    
    return render(request, 'treeapp/albums/view_album.html', {
        'album': album,
        'can_edit': can_edit
    })

@login_required
def edit_album(request, album_id):
    """View for editing an existing album"""
    album = get_object_or_404(Album, id=album_id)
    
    # Check if user can edit this album
    if album.user != request.user and not request.user.is_staff:
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        photos = request.FILES.getlist('photos')
        
        if title:
            album.title = title
            album.description = description
            album.is_approved = False  # Reset approval status on edit
            album.save()
            
            # Process uploaded photos
            for photo in photos:
                AlbumPhoto.objects.create(
                    album=album,
                    image=photo,
                    caption=''
                )
            
            return redirect('view_album', album_id=album.id)
    
    return render(request, 'treeapp/albums/edit_album.html', {'album': album})

@login_required
def update_profile(request):
    if request.method == 'POST':
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
        
        # Update basic profile information
        profile.name = request.POST.get('name', '')
        profile.father_name = request.POST.get('father_name', '')
        profile.phone = request.POST.get('phone', '')
        profile.blood_group = request.POST.get('blood_group', '')
        profile.is_blood_donor = request.POST.get('is_blood_donor') == 'on'
        profile.gender = request.POST.get('gender', '')
        
        # Handle marital status and anniversary date
        profile.marital_status = request.POST.get('marital_status', '')
        if profile.marital_status == 'married':
            anniversary = request.POST.get('anniversary_date')
            if anniversary:
                try:
                    profile.anniversary_date = datetime.strptime(anniversary, '%Y-%m-%d').date()
                except ValueError:
                    profile.anniversary_date = None
            else:
                profile.anniversary_date = None
        else:
            profile.anniversary_date = None # Clear anniversary if not married
        
        # Handle date of birth
        dob = request.POST.get('date_of_birth')
        if dob:
            try:
                profile.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                pass
        # Sync to FamilyMember node if linked
        if profile.member_id:
            profile.member_id.date_of_birth = profile.date_of_birth
            profile.member_id.save()
        
        # Handle profile picture
        if 'picture' in request.FILES:
            profile.picture = request.FILES['picture']
        
        # Handle email change
        new_email = request.POST.get('email')
        if new_email and new_email != request.user.email:
            # Generate OTP
            otp = ''.join(random.choices('0123456789', k=6))
            profile.email_verification_token = otp
            profile.save()
            
            # Send OTP email
            subject = 'Verify your new email address'
            message = f'Your OTP for email verification is: {otp}'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [new_email]
            
            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, 'OTP has been sent to your new email address.')
            except Exception as e:
                messages.error(request, 'Failed to send OTP. Please try again.')
                return redirect('user_dashboard')
            
            # Store new email in session for verification
            request.session['pending_email'] = new_email
            return redirect('verify_email')
        
        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('user_dashboard')
    
    return redirect('user_dashboard')

@login_required
def verify_email(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        pending_email = request.session.get('pending_email')
        
        if not pending_email:
            messages.error(request, 'No pending email verification.')
            return redirect('user_dashboard')
        
        profile = request.user.profile
        if profile.email_verification_token == otp:
            # Update email
            request.user.email = pending_email
            request.user.save()
            
            # Clear verification data
            profile.email_verification_token = None
            profile.email_verified = True
            profile.save()
            
            del request.session['pending_email']
            messages.success(request, 'Email updated successfully.')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
        
        return redirect('user_dashboard')
    
    return render(request, 'treeapp/verify_email.html')

@login_required
def calendar_page(request):
    user_profile = UserProfile.objects.get(user=request.user)
    calendar_events = []
    current_year = datetime.now().year

    # Create a dictionary to store events by date
    events_by_date = {}

    # Collect birthdays from FamilyMember model
    def collect_family_members(member):
        if member.date_of_birth:
            month = member.date_of_birth.month
            day = member.date_of_birth.day
            for year in range(current_year, current_year + 6):
                date_key = f"{year}-{month:02d}-{day:02d}"
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append({
                    "title": f"{member.name}'s Birthday",
                    "start": date_key,
                    "allDay": True,
                    "extendedProps": {
                        "type": "birthday"
                    },
                    "backgroundColor": "#4CAF50",
                    "borderColor": "#45a049",
                    "textColor": "#ffffff"
                })
        # Recursively collect children's birthdays
        for child in FamilyMember.objects.filter(parent=member):
            collect_family_members(child)

    # Start collecting from the root member
    if user_profile.family_root:
        collect_family_members(user_profile.family_root)

    # Collect anniversaries from UserProfile
    family_members = UserProfile.objects.filter(family_root=user_profile.family_root)
    for member in family_members:
        if member.marital_status == "married" and member.anniversary_date:
            month = member.anniversary_date.month
            day = member.anniversary_date.day
            for year in range(current_year, current_year + 6):
                date_key = f"{year}-{month:02d}-{day:02d}"
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append({
                    "title": f"{member.name}'s Anniversary",
                    "start": date_key,
                    "allDay": True,
                    "extendedProps": {
                        "type": "anniversary"
                    },
                    "backgroundColor": "#ff7e5f",
                    "borderColor": "#feb47b",
                    "textColor": "#ffffff"
                })

    # Add custom notifications
    custom_notifications = CustomNotification.objects.filter(
        is_active=True
    ).exclude(
        message__icontains='suspended'
    ).order_by('-created_at')

    for notification in custom_notifications:
        if notification.notification_date:
            date_key = notification.notification_date.strftime("%Y-%m-%d")
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append({
                "title": notification.message,
                "start": date_key,
                "allDay": True,
                "extendedProps": {
                    "type": "notification"
                },
                "backgroundColor": "#2196F3",
                "borderColor": "#1976D2",
                "textColor": "#ffffff"
            })

    # Flatten the events dictionary into a list
    for date_events in events_by_date.values():
        calendar_events.extend(date_events)

    return render(request, "treeapp/calendar_page.html", {
        "calendar_events": json.dumps(calendar_events)
    })

def donation_page(request):
    """View for displaying the donation page"""
    return render(request, 'treeapp/donation.html')

@login_required
def record_donation(request):
    """View for handling donation submissions"""
    if request.method == 'POST':
        try:
            donation = Donation.objects.create(
                name=request.POST.get('name'),
                amount=request.POST.get('amount'),
                transaction_id=request.POST.get('transaction_id'),
                donation_date=request.POST.get('donation_date')
            )
            return JsonResponse({
                'success': True,
                'name': donation.name
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def suspend_user(request, user_id):
    if not request.user.is_superuser:
        return redirect('user_dashboard')
    try:
        user = User.objects.get(id=user_id)
        profile = UserProfile.objects.get(user=user)
        # Toggle suspension status
        profile.is_suspended = not profile.is_suspended
        profile.save()
        status = "suspended" if profile.is_suspended else "unsuspended"
        messages.success(request, f'User {user.username} has been {status} successfully.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
    return redirect('admin_user_list')

@login_required
def deactivate_user(request, user_id):
    if not request.user.is_superuser:
        return redirect('user_dashboard')
    try:
        user = User.objects.get(id=user_id)
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} has been deactivated successfully.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    return redirect('admin_user_list')

@login_required
def activate_user(request, user_id):
    if not request.user.is_superuser:
        return redirect('user_dashboard')
    try:
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()
        messages.success(request, f'User {user.username} has been activated successfully.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    return redirect('admin_user_list')

@login_required
def user_login_info(request, user_id):
    if not request.user.is_superuser:
        return redirect('user_dashboard')
    
    try:
        target_user = User.objects.get(id=user_id)
        login_info = UserLoginInfo.objects.filter(user=target_user).order_by('-login_time')
        
        # Calculate durations for each session
        for session in login_info:
            if session.logout_time:
                session.duration = session.logout_time - session.login_time
            else:
                session.duration = timezone.now() - session.login_time
            
            # Calculate days, hours, minutes
            total_seconds = session.duration.total_seconds()
            days = int(total_seconds // 86400)
            hours = int((total_seconds % 86400) // 3600)
            minutes = int((total_seconds % 3600) // 60)
            
            # Format duration string
            duration_parts = []
            if days > 0:
                duration_parts.append(f"{days}d")
            if hours > 0:
                duration_parts.append(f"{hours}h")
            if minutes > 0:
                duration_parts.append(f"{minutes}m")
            
            session.formatted_duration = " ".join(duration_parts) if duration_parts else "-"
        
        total_sessions = login_info.count()
        current_session = login_info.filter(logout_time__isnull=True).first()
        
        context = {
            'user': target_user,
            'login_info': login_info,
            'total_sessions': total_sessions,
            'current_session': current_session,
        }
        return render(request, 'treeapp/user_login_info.html', context)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('admin_user_list')

@login_required
def admin_user_list(request):
    if not request.user.is_superuser:
        return redirect('user_dashboard')

    # Get all users
    users = User.objects.all().order_by('-date_joined')
    
    # Calculate user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    suspended_users = User.objects.filter(userprofile__is_suspended=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    logger.debug(f"Total Users: {total_users}")
    logger.debug(f"Active Users: {active_users}")
    logger.debug(f"Inactive Users: {inactive_users}")
    logger.debug(f"Suspended Users: {suspended_users}")
    logger.debug(f"Superusers: {superusers}")

    user_data = []
    for user in users:
        try:
            profile = user.userprofile
        except UserProfile.DoesNotExist:
            profile = None

        user_data.append({
            'id': user.id,
            'username': user.username,
            'name': profile.name if profile else '',
            'father_name': profile.father_name if profile else '',
            'email': user.email,
            'phone': profile.phone if profile else '',
            'plain_password': profile.plain_password if profile else '',
            'is_active': user.is_active,
            'email_verified': profile.email_verified if profile else False,
            'userprofile': profile,  # Add the entire profile object
        })

    # Dashboard card counts
    total_posts = Post.objects.count()
    pending_posts_count = Post.objects.filter(is_approved=False).count()
    total_albums = Album.objects.count()
    pending_albums_count = Album.objects.filter(is_approved=False).count()

    context = {
        'user_data': user_data,
        'total_posts': total_posts,
        'pending_posts_count': pending_posts_count,
        'total_albums': total_albums,
        'pending_albums_count': pending_albums_count,
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'suspended_users': suspended_users,
        'superusers': superusers,
    }
    return render(request, 'treeapp/admin_user_list.html', context)