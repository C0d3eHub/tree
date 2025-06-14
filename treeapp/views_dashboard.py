from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import FamilyMember, UserProfile, Post, Album, AlbumPhoto, CustomNotification, Donation
import json
from datetime import datetime
import random
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.contrib.auth.models import User

@login_required
def user_dashboard(request):
    """
    Main dashboard view that shows the user's tree, posts, and albums in tabs
    """
    # Get the user's profile data
    try:
        user_profile = request.user.userprofile
        user_root = user_profile.family_root
        member_id = user_profile.member_id
    except (UserProfile.DoesNotExist, AttributeError):
        user_root = None
        member_id = None
        user_profile = None

    # Get user's posts
    user_posts = Post.objects.filter(user=request.user).order_by('-created_at')
    
    # Get user's albums
    user_albums = Album.objects.filter(user=request.user).order_by('-created_at')
    
    # Check if user has a tree
    no_tree = user_root is None
    
    tree_data = {}
    if not no_tree:
        # Build direct lineage tree
        def build_direct_lineage():
            # Find the main root (topmost ancestor)
            main_root = None
            current = user_root
            ancestors = []
            
            # Traverse up to find all ancestors
            while current:
                ancestors.append(current)
                if current.parent is None:
                    main_root = current
                    break
                current = current.parent
            
            # Reverse to get top-down order
            ancestors.reverse()
            
            # Start with the main root
            if not main_root:
                return None
                
            # Create the tree structure
            tree = {
                "id": main_root.id,
                "name": main_root.name,
                "father_name": None,
                "year_of_birth": main_root.year_of_birth if main_root.year_of_birth else None,
                "year_of_death": main_root.year_of_death if main_root.year_of_death else None,
                "picture": main_root.photo.url if main_root.photo else "",
                "is_main_root": True,
                "children": []
            }
            
            # Helper function to add all descendants of a member
            def add_descendants(node, member):
                children = FamilyMember.objects.filter(parent=member)
                for child in children:
                    child_node = {
                        "id": child.id,
                        "name": child.name,
                        "father_name": member.name,
                        "year_of_birth": child.year_of_birth if child.year_of_birth else None,
                        "year_of_death": child.year_of_death if child.year_of_death else None,
                        "picture": child.photo.url if child.photo else "",
                        "children": []
                    }
                    node["children"].append(child_node)
                    # Recursively add all descendants
                    add_descendants(child_node, child)
            
            # If member_id is specified, build path from root to member_id
            if member_id:
                # Find path from root to member_id
                path_to_member = []
                current = member_id
                
                # Build the path up to root
                while current:
                    path_to_member.append(current)
                    if current.parent is None:
                        break
                    current = current.parent
                
                # Reverse to get top-down order
                path_to_member.reverse()
                
                # Build the complete tree structure
                current_node = tree
                for i in range(1, len(path_to_member)):
                    ancestor = path_to_member[i]
                    # Find the correct parent node to attach this ancestor to
                    parent_node = None
                    if i == 1:
                        parent_node = current_node
                    else:
                        # Find the parent node in the tree
                        def find_parent_node(node, parent_id):
                            if node["id"] == parent_id:
                                return node
                            for child in node["children"]:
                                result = find_parent_node(child, parent_id)
                                if result:
                                    return result
                            return None
                        parent_node = find_parent_node(tree, path_to_member[i-1].id)
                    
                    if parent_node:
                        new_node = {
                            "id": ancestor.id,
                            "name": ancestor.name,
                            "father_name": path_to_member[i-1].name,
                            "year_of_birth": ancestor.year_of_birth if ancestor.year_of_birth else None,
                            "year_of_death": ancestor.year_of_death if ancestor.year_of_death else None,
                            "picture": ancestor.photo.url if ancestor.photo else "",
                            "is_user_root": ancestor.id == user_root.id,
                            "is_member_id": ancestor.id == member_id.id,
                            "children": []
                        }
                        parent_node["children"].append(new_node)
                        current_node = new_node
                
                # Add all descendants of member_id
                add_descendants(current_node, member_id)
            else:
                # If no member_id, fall back to user_root
                current_node = tree
                for i in range(1, len(ancestors)):
                    ancestor = ancestors[i]
                    new_node = {
                        "id": ancestor.id,
                        "name": ancestor.name,
                        "father_name": ancestors[i-1].name,
                        "year_of_birth": ancestor.year_of_birth if ancestor.year_of_birth else None,
                        "year_of_death": ancestor.year_of_death if ancestor.year_of_death else None,
                        "picture": ancestor.photo.url if ancestor.photo else "",
                        "is_user_root": ancestor.id == user_root.id,
                        "children": []
                    }
                    current_node["children"].append(new_node)
                    current_node = new_node
                
                # Add all descendants of user_root
                add_descendants(current_node, user_root)
            
            return tree
        
        # Build the direct lineage tree
        tree_data = build_direct_lineage() or {}
    
    # Find ancestors to determine which ones are editable (last 2 roots)
    editable_ancestors = []
    if member_id:
        try:
            # Start with member_id
            current = member_id
            depth = 0
            
            # Get the last 2 ancestors
            while current and depth < 2:
                editable_ancestors.append(current.id)
                if not current.parent:
                    break
                current = current.parent
                depth += 1
        except Exception as e:
            print(f"Error finding editable ancestors: {e}")
    
    member_id_value = None
    if member_id:
        try:
            member_id_value = member_id.id
        except:
            member_id_value = None
    
    # Get today's date
    today = datetime.today()
    # Find all FamilyMembers whose birthday is today
    birthday_members = FamilyMember.objects.filter(date_of_birth__month=today.month, date_of_birth__day=today.day)
    
    # Find all UserProfiles whose anniversary is today and are married
    anniversary_members = UserProfile.objects.filter(
        marital_status='married',
        anniversary_date__month=today.month,
        anniversary_date__day=today.day
    )
    
    # Use FamilyMember's date_of_birth for birthday message for the logged-in user
    is_birthday = False
    member = user_profile.member_id if user_profile and user_profile.member_id else None
    if member and member.date_of_birth:
        is_birthday = (member.date_of_birth.month == today.month and member.date_of_birth.day == today.day)
    elif not user_profile and birthday_members.exists():
        is_birthday = True
    
    # Get active custom notifications
    custom_notifications = CustomNotification.objects.filter(is_active=True)
    
    # Collect calendar events (birthdays and anniversaries)
    calendar_events = []
    
    # 1. Get all family members in the user's tree
    family_members = []
    if user_profile and user_profile.family_root:
        def collect_members(member):
            family_members.append(member)
            for child in FamilyMember.objects.filter(parent=member):
                collect_members(child)
        collect_members(user_profile.family_root)

    # 2. Collect birthdays
    for member in family_members:
        if member.date_of_birth:
            # Get the month and day from the date of birth
            month = member.date_of_birth.month
            day = member.date_of_birth.day
            
            # Create a recurring event for each year
            calendar_events.append({
                "type": "birthday",
                "name": f"{member.name}'s Birthday",  # Add 's Birthday to make it clearer
                "date": f"2024-{month:02d}-{day:02d}",  # Use current year as base
                "color": "#4CAF50",
                "backgroundColor": "#4CAF50",
                "borderColor": "#45a049",
                "textColor": "#ffffff",
                "rrule": "FREQ=YEARLY",  # Make it repeat yearly
                "display": "block"
            })

    # 3. Collect anniversary (if married)
    if user_profile and user_profile.marital_status == "married" and user_profile.anniversary_date:
        # Get the month and day from the anniversary date
        month = user_profile.anniversary_date.month
        day = user_profile.anniversary_date.day
        
        # Create a recurring event for each year
        calendar_events.append({
            "type": "anniversary",
            "name": f"{user_profile.name or user_profile.user.get_full_name() or user_profile.user.username}'s Anniversary",  # Add 's Anniversary to make it clearer
            "date": f"2024-{month:02d}-{day:02d}",  # Use current year as base
            "color": "#4CAF50",
            "backgroundColor": "#4CAF50",
            "borderColor": "#45a049",
            "textColor": "#ffffff",
            "rrule": "FREQ=YEARLY",  # Make it repeat yearly
            "display": "block"
        })
    
    return render(request, "treeapp/user_dashboard.html", {
        "user": request.user,
        "user_profile": user_profile,
        "user_posts": user_posts,
        "user_albums": user_albums,
        "tree_data_json": json.dumps(tree_data) if tree_data else None,
        "no_tree": no_tree,
        "editable_ancestors": json.dumps(editable_ancestors),
        "member_id": member_id_value,
        "is_birthday": is_birthday,
        "birthday_members": birthday_members,
        "other_birthday_users": [],
        'custom_notifications': custom_notifications,
        'anniversary_members': anniversary_members,
        'calendar_events': json.dumps(calendar_events, cls=DjangoJSONEncoder),
    })

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

    # Collect all family members in the user's tree
    family_members = []
    if user_profile and user_profile.family_root:
        def collect_members(member):
            family_members.append(member)
            for child in FamilyMember.objects.filter(parent=member):
                collect_members(child)
        collect_members(user_profile.family_root)

    # Collect birthdays
    for member in family_members:
        if member.date_of_birth:
            # Get the month and day from the date of birth
            month = member.date_of_birth.month
            day = member.date_of_birth.day
            
            # Create events for current year and next 5 years
            for year in range(current_year, current_year + 6):
                calendar_events.append({
                    "title": f"{member.name}'s Birthday",
                    "start": f"{year}-{month:02d}-{day:02d}",
                    "allDay": True,
                    "extendedProps": {
                        "type": "birthday"
                    },
                    "backgroundColor": "#4CAF50",
                    "borderColor": "#45a049",
                    "textColor": "#ffffff"
                })

    # Collect anniversary (if married)
    if user_profile and user_profile.marital_status == "married" and user_profile.anniversary_date:
        # Get the month and day from the anniversary date
        month = user_profile.anniversary_date.month
        day = user_profile.anniversary_date.day
        
        # Create events for current year and next 5 years
        for year in range(current_year, current_year + 6):
            calendar_events.append({
                "title": f"{user_profile.name or user_profile.user.get_full_name() or user_profile.user.username}'s Anniversary",
                "start": f"{year}-{month:02d}-{day:02d}",
                "allDay": True,
                "extendedProps": {
                    "type": "anniversary"
                },
                "backgroundColor": "#4CAF50",
                "borderColor": "#45a049",
                "textColor": "#ffffff"
            })

    return render(request, "treeapp/calendar_page.html", {
        "calendar_events": json.dumps(calendar_events, cls=DjangoJSONEncoder),
        "user_profile": user_profile,
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