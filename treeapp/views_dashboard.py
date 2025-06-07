from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import FamilyMember, UserProfile, Post, Album, AlbumPhoto
import json

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

    # Get user's posts
    user_posts = Post.objects.filter(user=request.user).order_by('-created_at')
    
    # Get user's albums
    user_albums = Album.objects.filter(user=request.user).order_by('-created_at')
    
    # Check if user has a tree
    no_tree = user_root is None
    
    # Build tree data if user has a tree
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
    
    return render(request, "treeapp/user_dashboard.html", {
        "user": request.user,
        "user_posts": user_posts,
        "user_albums": user_albums,
        "tree_data_json": json.dumps(tree_data) if tree_data else None,
        "no_tree": no_tree,
        "editable_ancestors": json.dumps(editable_ancestors),
        "member_id": member_id_value,
    })

@login_required
def add_post(request):
    """View for creating a new post"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category = request.POST.get('category')
        
        if title and content and category:
            post = Post.objects.create(
                title=title,
                content=content,
                category=category,
                user=request.user,
                is_approved=False  # Posts need approval by default
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
def create_album(request):
    """View for creating a new album"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        photos = request.FILES.getlist('photos')
        
        if title:
            album = Album.objects.create(
                title=title,
                description=description,
                user=request.user,
                is_approved=False  # Albums need approval by default
            )
            
            # Process uploaded photos
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