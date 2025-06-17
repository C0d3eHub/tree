from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import FamilyMember, Correction, Album, AlbumPhoto, Post, UserLoginInfo, CommitteeMember
from .forms import AlbumForm, AlbumPhotoForm, PostForm
from django.contrib.auth.decorators import login_required
import json
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
import logging
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)

def build_tree(member):
    children = list(FamilyMember.objects.filter(parent=member))
    return {
        "name": member.name,
        "id": member.id,
        "father_name": member.parent.name if member.parent else None,
        "date_of_birth": member.date_of_birth.isoformat() if member.date_of_birth else None,
        "year_of_birth": member.year_of_birth,
        "year_of_death": member.year_of_death,
        "picture": member.photo.url if member.photo else None,
        "children": [build_tree(child) for child in children],
        "_children": []
    }


def tree_view(request):
    """Render the tree HTML template with root member's name and tree data."""
    root = FamilyMember.objects.filter(parent__isnull=True).first()
    if not root:
        return render(request, 'treeapp/tree.html', {'tree_data': '{}', 'family_name': 'Family Tree'})

    try:
        tree_data = build_tree(root)
        return render(request, 'treeapp/tree.html', {
            'tree_data': json.dumps(tree_data),
            'family_name': root.name
        })
    except Exception as e:
        print(f"Error building tree: {e}")
        return render(request, 'treeapp/tree.html', {
            'tree_data': '{}',
            'family_name': root.name if root else 'Family Tree',
            'error': str(e)
        })

def tree_data(request):
    """API endpoint for fetching tree data as JSON."""
    root = FamilyMember.objects.filter(parent__isnull=True).first()
    if not root:
        return JsonResponse({})
    try:
        data = build_tree(root)
        return JsonResponse(data, safe=False)
    except Exception as e:
        print(f"Error building tree: {e}")
        return JsonResponse({"error": str(e)}, status=500)

def index(request):
    return render(request, 'treeapp/index.html')
    
def instructions_view(request):
    return render(request, 'treeapp/instructions.html')

def posts_view(request):
    # Get approved posts
    approved_posts = Post.objects.filter(is_approved=True).order_by('-created_at')
    return render(request, 'treeapp/posts.html', {'posts': approved_posts})
    
@login_required
def add_album(request):
    if request.method == 'POST':
        form = AlbumForm(request.POST)
        if form.is_valid():
            album = form.save(commit=False)
            album.user = request.user
            album.save()
            return render(request, 'treeapp/add_album.html', {
                'album': album,
                'photo_form': AlbumPhotoForm(),
                'photos': []
            })
    else:
        form = AlbumForm()
    return render(request, 'treeapp/add_album.html', {'form': form})

@login_required
def add_photo(request, album_id):
    album = Album.objects.get(id=album_id)
    if album.user != request.user and not request.user.is_superuser:
        return redirect('my_albums')
        
    if request.method == 'POST':
        form = AlbumPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.album = album
            photo.save()
    
    photos = AlbumPhoto.objects.filter(album=album)
    return render(request, 'treeapp/add_album.html', {
        'album': album,
        'photo_form': AlbumPhotoForm(),
        'photos': photos
    })

@login_required
def my_albums(request):
    albums = Album.objects.filter(user=request.user)
    return render(request, 'treeapp/my_albums.html', {'albums': albums})

def view_album(request, album_id):
    album = get_object_or_404(Album, id=album_id)
    photos = AlbumPhoto.objects.filter(album=album)
    
    # Check if the user is the owner or a superuser to show edit option
    can_edit = request.user.is_authenticated and (
        album.user == request.user or request.user.is_superuser
    )
    
    return render(request, 'treeapp/gallery.html', {
        'album': album, 
        'photos': photos,
        'can_edit': can_edit
    })

@login_required
def edit_album(request, album_id):
    album = Album.objects.get(id=album_id)
    if album.user != request.user and not request.user.is_superuser:
        return redirect('my_albums')
        
    if request.method == 'POST':
        form = AlbumForm(request.POST, instance=album)
        if form.is_valid():
            form.save()
            return redirect('my_albums')
    else:
        form = AlbumForm(instance=album)
    
    return render(request, 'treeapp/edit_album.html', {'form': form, 'album': album})

@csrf_exempt
def submit_correction(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        original = data.get('original')
        corrected = data.get('corrected')
        Correction.objects.create(original_name=original, corrected_name=corrected)
        return JsonResponse({'status': 'ok'})

from django.shortcuts import render, redirect
from .forms import AddMemberForm

def add_member(request):
    success = False
    if request.method == 'POST':
        form = AddMemberForm(request.POST)
        if form.is_valid():
            form.save()
            # After saving, render with success context (do not show form)
            return render(request, 'treeapp/add_member.html', {'success': True})
    else:
        form = AddMemberForm()
    return render(request, 'treeapp/add_member.html', {'form': form, 'success': False})


def gallery_view(request):
    # Get approved albums
    approved_albums = Album.objects.filter(is_approved=True).order_by('-created_at')
    
    # Fallback list of images if no albums are approved
    image_list = []
    if not approved_albums.exists():
        image_list = [
            'treeapp/images/image1.jpg',
            'treeapp/images/image2.jpg',
            'treeapp/images/image3.jpg',
            'treeapp/images/image4.jpg',
            'treeapp/images/image6.jpg',
            'treeapp/images/image7.jpg',
            'treeapp/images/image8.jpg',
            'treeapp/images/image9.jpg',
            'treeapp/images/image10.jpg',
            'treeapp/images/image11.jpg',
            'treeapp/images/image12.jpg',
            'treeapp/images/image13.jpg',
            'treeapp/images/image14.jpg',
            'treeapp/images/image15.jpg',
            'treeapp/images/image16.jpg',
            'treeapp/images/image17.jpg',
            'treeapp/images/image18.jpg',
            'treeapp/images/image19.jpg',
            'treeapp/images/image20.jpg',
        ]
    
    return render(request, 'treeapp/gallery.html', {
        'image_list': image_list,
        'albums': approved_albums
    })


from django.shortcuts import render, redirect
from .forms import HelpRequestForm

def help_view(request):
    submitted = False
    if request.method == "POST":
        form = HelpRequestForm(request.POST)
        if form.is_valid():
            form.save()
            submitted = True
            form = HelpRequestForm()  # reset form after submission
    else:
        form = HelpRequestForm()
    context = {
        'form': form,
        'submitted': submitted,
        'contact_email': 'kmmbanjani@gmail.com',
        'contact_phone': '+91-updating soon'
    }
    return render(request, 'treeapp/help.html', context)


from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .forms import AddMultipleChildrenForm
from .models import FamilyMember
from django.contrib import messages

@staff_member_required
def add_multiple_children(request):
    if request.method == "POST":
        form = AddMultipleChildrenForm(request.POST)
        if form.is_valid():
            parent = form.cleaned_data['parent']
            children_names = [
                form.cleaned_data['child_1'],
                form.cleaned_data['child_2'],
                form.cleaned_data['child_3'],
                form.cleaned_data['child_4'],
                form.cleaned_data['child_5'],
                form.cleaned_data['child_6'],
                form.cleaned_data['child_7'],
            ]
            added = 0
            for name in children_names:
                if name.strip():
                    FamilyMember.objects.create(name=name.strip(), parent=parent)
                    added += 1
            if added:
                messages.success(request, f"Successfully added {added} child{'ren' if added > 1 else ''} to {parent.name}.")
            else:
                messages.info(request, "No child names were entered.")
            return redirect('index')  # Update with your index view name
    else:
        form = AddMultipleChildrenForm()
    return render(request, 'treeapp/add_multiple_children.html', {'form': form})

from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from .models import UserProfile, FamilyMember

import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User needs admin approval
            user.email = form.cleaned_data.get('email')  # Save email for password reset
            
            # Get the plain password before it's hashed
            plain_password = form.cleaned_data.get('password1')
            
            user.save()
            
            # Generate verification token
            verification_token = str(uuid.uuid4())
            
            # Store name, father's name, phone, and plain password in UserProfile
            name = form.cleaned_data.get('name')
            father_name = form.cleaned_data.get('father_name')
            phone = form.cleaned_data.get('phone')
            gender = form.cleaned_data.get('gender')
            date_of_birth = form.cleaned_data.get('date_of_birth')
            
            UserProfile.objects.create(
                user=user, 
                name=name,
                father_name=father_name,
                phone=phone,
                gender=gender,
                date_of_birth=date_of_birth,
                plain_password=plain_password,  # Store the plain password
                email_verification_token=verification_token
            )
            
            # Send verification email
            try:
                verification_url = request.build_absolute_uri(
                    reverse('verify_email', args=[verification_token])
                )
                
                send_mail(
                    'Verify your email for Family Tree',
                    f'Please click the link below to verify your email address:\n\n{verification_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Failed to send verification email: {e}")
            
            # Show success message
            return render(request, 'treeapp/register_success.html', {
                'username': user.username,
                'name': name,
                'father_name': father_name,
                'email': user.email,
                'verification_sent': True
            })
    else:
        form = RegisterForm()
    return render(request, 'treeapp/register.html', {'form': form})

from django.contrib.auth.models import User

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # First check if user exists
        try:
            user = User.objects.get(username=username)
            if not user.is_active:
                messages.error(request, 'Your account is deactivated. Please contact the administrator for assistance.')
                return redirect('login')
            try:
                if user.userprofile.is_suspended:
                    messages.error(request, 'Your account has been suspended. Please contact the administrator for assistance.')
                    return redirect('login')
            except UserProfile.DoesNotExist:
                pass
        except User.DoesNotExist:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
            
        # Now try to authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Record login info
            UserLoginInfo.objects.create(
                user=user,
                login_time=timezone.now(),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'treeapp/login.html')

def logout_view(request):
    if request.user.is_authenticated:
        # Update the last login info with logout time
        last_login = UserLoginInfo.objects.filter(user=request.user, logout_time__isnull=True).first()
        if last_login:
            last_login.logout_time = timezone.now()
            last_login.save()
    logout(request)
    return redirect('login')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import FamilyMember, UserProfile
import json

@login_required
def my_family_tree(request, user_id=None):
    # If user_id is provided and user is superuser, get that user's profile
    if user_id and request.user.is_superuser:
        try:
            target_user = User.objects.get(id=user_id)
            user_profile = target_user.userprofile
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            return render(request, "treeapp/error.html", {
                'error': "User not found",
                'message': "The requested user does not exist.",
                'back_url': 'user_dashboard'
            })
    else:
        # Get the current user's profile
        try:
            user_profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            user_profile = None

    # Get the user's family root, last child, and member_id
    try:
        user_root = user_profile.family_root
        last_child = user_profile.last_child
        member_id = user_profile.member_id
    except (UserProfile.DoesNotExist, AttributeError):
        user_root = None
        last_child = None
        member_id = None
    except Exception as e:
        print(f"Error accessing user profile: {e}")
        user_root = None
        last_child = None
        member_id = None

    if not user_root:
        # User has no root assigned
        return render(request, "treeapp/my_tree.html", {
            "tree_data_json": None,
            "family_name": "",
            "no_tree": True,
        })

    # Find the main root (id=1) or the topmost ancestor
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
    
    # Build a direct lineage tree from main root to member_id, then all children of member_id
    def build_direct_lineage():
        # Start with the main root
        if not main_root:
            return None
            
        # Create the tree structure
        tree = {
            "id": main_root.id,
            "name": main_root.name,
            "father_name": None,
            "year_of_birth": main_root.year_of_birth,
            "year_of_death": main_root.year_of_death,
            "picture": main_root.photo.url if main_root.photo else "",
            "is_main_root": True,
            "children": []
        }
        
        # Current node in the tree we're building
        current_node = tree
        
        # Helper function to add all descendants of a member
        def add_descendants(node, member):
            children = FamilyMember.objects.filter(parent=member)
            for child in children:
                child_node = {
                    "id": child.id,
                    "name": child.name,
                    "father_name": member.name,
                    "year_of_birth": child.year_of_birth,
                    "year_of_death": child.year_of_death,
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
            
            # Add each ancestor in the direct lineage
            for i in range(1, len(path_to_member)):
                ancestor = path_to_member[i]
                new_node = {
                    "id": ancestor.id,
                    "name": ancestor.name,
                    "father_name": path_to_member[i-1].name,
                    "year_of_birth": ancestor.year_of_birth,
                    "year_of_death": ancestor.year_of_death,
                    "picture": ancestor.photo.url if ancestor.photo else "",
                    "is_user_root": ancestor.id == user_root.id,
                    "is_member_id": ancestor.id == member_id.id,
                    "children": []
                }
                current_node["children"] = [new_node]
                current_node = new_node
            
            # Add all descendants of member_id
            add_descendants(current_node, member_id)
        else:
            # If no member_id, fall back to user_root
            # Add each ancestor in the direct lineage to user_root
            for i in range(1, len(ancestors)):
                ancestor = ancestors[i]
                new_node = {
                    "id": ancestor.id,
                    "name": ancestor.name,
                    "father_name": ancestors[i-1].name,
                    "year_of_birth": ancestor.year_of_birth,
                    "year_of_death": ancestor.year_of_death,
                    "picture": ancestor.photo.url if ancestor.photo else "",
                    "is_user_root": ancestor.id == user_root.id,
                    "children": []
                }
                current_node["children"] = [new_node]
                current_node = new_node
            
            # Add all descendants of user_root
            add_descendants(current_node, user_root)
        
        return tree
        
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
    
    # After you set user_profile (for the tree owner)
    tree_owner_id = None
    if user_profile and hasattr(user_profile, 'user'):
        tree_owner_id = user_profile.user.id
    else:
        tree_owner_id = request.user.id

    return render(request, "treeapp/my_tree.html", {
        "tree_data_json": json.dumps(tree_data) if tree_data else None,
        "family_name": user_root.name if user_root else "",
        "no_tree": False,
        "editable_ancestors": json.dumps(editable_ancestors),
        "member_id": member_id_value,
        "tree_owner_id": tree_owner_id,
    })

from django.shortcuts import render, redirect
from .models import FamilyMember
from .forms import FamilyMemberForm
from django.contrib.auth.decorators import login_required
@login_required
def edit_member(request, member_id):
    member = FamilyMember.objects.get(id=member_id)
    
    # Superusers can edit all members
    if request.user.is_superuser:
        if request.method == 'POST':
            form = FamilyMemberForm(request.POST, request.FILES, instance=member)
            if form.is_valid():
                form.save()
                return redirect('user_dashboard')
        else:
            form = FamilyMemberForm(instance=member)
        
        return render(request, 'treeapp/edit_member.html', {
            'form': form, 
            'member': member,
            'is_superuser': True
        })
    
    # Regular users can only edit their member_id, children, and 2 recent ancestors
    try:
        user_profile = request.user.userprofile
        user_member_id = user_profile.member_id
    except (UserProfile.DoesNotExist, AttributeError):
        user_member_id = None
    
    if not user_member_id:
        return render(request, 'treeapp/error.html', {'error': "No member ID assigned to your profile"})
    
    # Check if member is editable (last 2 roots or descendants of member_id)
    def is_editable(member, user_member_id):
        # Check if member is member_id itself
        if member.id == user_member_id.id:
            return True
            
        # Check if member is a direct child of user_member_id
        if member.parent and member.parent.id == user_member_id.id:
            return True
            
        # Check if member is a descendant of user_member_id
        def is_descendant(parent_id, child):
            if not child.parent:
                return False
            if child.parent.id == parent_id:
                return True
            return is_descendant(parent_id, child.parent)
            
        # Check if member is a descendant
        if is_descendant(user_member_id.id, member):
            return True
            
        # Check if member is the parent of user_member_id
        if user_member_id.parent and member.id == user_member_id.parent.id:
            return True
            
        # Check if member is the grandparent of user_member_id
        if (user_member_id.parent and user_member_id.parent.parent and 
            member.id == user_member_id.parent.parent.id):
            return True
            
        return False
    
    # Check if user can edit this member
    if not is_editable(member, user_member_id):
        return render(request, 'treeapp/error.html', {
            'error': "Access Denied",
            'message': "You don't have permission to edit this member. You can only edit your own profile, your children, and up to 2 recent ancestors.",
            'back_url': 'user_dashboard'
        })
    
    if request.method == 'POST':
        form = FamilyMemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            # Sync to UserProfile if this member is the user's member_id
            if request.user.is_authenticated:
                try:
                    profile = request.user.userprofile
                    if profile.member_id and profile.member_id.id == member.id:
                        profile.date_of_birth = member.date_of_birth
                        profile.save()
                except UserProfile.DoesNotExist:
                    pass
            return redirect('user_dashboard')
    else:
        form = FamilyMemberForm(instance=member)
    
    return render(request, 'treeapp/edit_member.html', {
        'form': form, 
        'member': member,
        'is_superuser': False,
        'message': "Dear user, you can edit all your children and just 2 recent root parents."
    })

@csrf_exempt
@login_required
def upload_tree_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Generate unique filename
            filename = f"tree_images/{uuid.uuid4()}.png"
            
            # Save the file
            file = request.FILES['image']
            path = default_storage.save(filename, ContentFile(file.read()))
            
            # Get the URL
            url = request.build_absolute_uri(default_storage.url(path))
            
            return JsonResponse({
                'success': True,
                'url': url
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    }, status=400)

@staff_member_required
def admin_user_list(request):
    users = User.objects.all().order_by('-date_joined')
    
    # Calculate user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    suspended_users = User.objects.filter(is_active=False, userlogininfo__is_suspended=True).count()
    superusers = User.objects.filter(is_superuser=True).count()

    logger.debug(f"Total Users: {total_users}")
    logger.debug(f"Active Users: {active_users}")
    logger.debug(f"Inactive Users: {inactive_users}")
    logger.debug(f"Suspended Users: {suspended_users}")
    logger.debug(f"Superusers: {superusers}")
    
    context = {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'suspended_users': suspended_users,
        'superusers': superusers,
    }
    return render(request, 'treeapp/admin_user_list.html', context)


from django.shortcuts import render

def committee_page(request):
    members_list = CommitteeMember.objects.all().order_by('name')
    paginator = Paginator(members_list, 20)  # Show 20 members per page
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'treeapp/committee.html', context)
