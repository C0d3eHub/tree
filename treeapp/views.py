from django.shortcuts import render
from django.http import JsonResponse
from .models import FamilyMember, Correction
import json
from django.views.decorators.csrf import csrf_exempt

def build_tree(member):
    """Recursively build a nested dictionary representing the tree."""
    children = FamilyMember.objects.filter(parent=member)
    return {
        "name": member.name,
        "id": member.id,
        "children": [build_tree(child) for child in children]
    }

def tree_view(request):
    """Render the tree HTML template with root member's name and tree data."""
    root = FamilyMember.objects.filter(parent__isnull=True).first()
    if not root:
        return render(request, 'treeapp/tree.html', {'tree_data': '{}', 'family_name': 'Family Tree'})

    tree_data = build_tree(root)
    return render(request, 'treeapp/tree.html', {
        'tree_data': json.dumps(tree_data),
        'family_name': root.name
    })

def tree_data(request):
    """API endpoint for fetching tree data as JSON."""
    root = FamilyMember.objects.filter(parent__isnull=True).first()
    if not root:
        return JsonResponse({})
    data = build_tree(root)
    return JsonResponse(data, safe=False)

def index(request):
    return render(request, 'treeapp/index.html')

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
        # Add more images as needed
    ]
    return render(request, 'treeapp/gallery.html', {'image_list': image_list})


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