from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import FamilyMember, UserProfile, Post, Album
import json
from datetime import date

@login_required
def user_profile(request, tab=None):
    """
    Display the user profile with tabs for MyTree, Posts, and Albums
    """
    # Set default active tab if none provided
    if not tab or tab not in ['mytree', 'posts', 'albums']:
        tab = 'mytree'
    
    # Get user profile data
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = None
    
    # Check if it's the user's birthday
    is_birthday = False
    if user_profile and user_profile.date_of_birth:
        today = date.today()
        is_birthday = (user_profile.date_of_birth.month == today.month and 
                      user_profile.date_of_birth.day == today.day)
    
    # Get user's posts
    user_posts = Post.objects.filter(user=request.user).order_by('-created_at')
    
    # Get user's albums
    user_albums = Album.objects.filter(user=request.user).order_by('-created_at')
    
    # Get tree data for MyTree tab
    tree_data = None
    member_id = None
    editable_ancestors = []
    no_tree = True
    
    if user_profile:
        # Get the user's family root, last child, and member_id
        user_root = user_profile.family_root
        last_child = user_profile.last_child
        member_id = user_profile.member_id
        
        if user_root:
            no_tree = False
            
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
            
            # Build the direct lineage tree
            tree_data = build_direct_lineage() or {}

            # Find ancestors to determine which ones are editable (last 2 roots)
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
    
    # Prepare member_id value for template
    member_id_value = None
    if member_id:
        try:
            member_id_value = member_id.id
        except:
            member_id_value = None
    
    # Render the profile template with appropriate context
    context = {
        'user_profile': user_profile,
        'active_tab': tab,
        'user_posts': user_posts,
        'user_albums': user_albums,
        'tree_data_json': json.dumps(tree_data) if tree_data else None,
        'no_tree': no_tree,
        'editable_ancestors': json.dumps(editable_ancestors),
        'member_id': member_id_value,
        'is_birthday': is_birthday,
    }
    
    return render(request, 'treeapp/user_profile.html', context)