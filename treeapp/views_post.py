from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import PostForm
from .models import Post

@login_required
def add_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('my_posts')
    else:
        form = PostForm()
    return render(request, 'treeapp/add_post.html', {'form': form})

@login_required
def my_posts(request):
    posts = Post.objects.filter(user=request.user)
    return render(request, 'treeapp/my_posts.html', {'posts': posts})

@login_required
def view_post(request, post_id):
    post = Post.objects.get(id=post_id)
    return render(request, 'treeapp/view_post.html', {'post': post})

@login_required
def edit_post(request, post_id):
    post = Post.objects.get(id=post_id)
    if post.user != request.user and not request.user.is_superuser:
        return redirect('my_posts')
        
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('my_posts')
    else:
        form = PostForm(instance=post)
    
    return render(request, 'treeapp/edit_post.html', {'form': form, 'post': post})