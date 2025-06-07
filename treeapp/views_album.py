from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import AlbumForm, AlbumPhotoForm
from .models import Album, AlbumPhoto

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

@login_required
def view_album(request, album_id):
    album = Album.objects.get(id=album_id)
    photos = AlbumPhoto.objects.filter(album=album)
    return render(request, 'treeapp/gallery.html', {'album': album, 'photos': photos})

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