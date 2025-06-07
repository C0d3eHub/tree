from django.contrib import admin
from .models import FamilyMember, Correction, AddMember, HelpRequest, UserProfile, BloodRequest, Album, AlbumPhoto, Post

@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'year_of_birth', 'year_of_death')
    search_fields = ('name',)
    list_filter = ('year_of_birth', 'year_of_death')

@admin.register(Correction)
class CorrectionAdmin(admin.ModelAdmin):
    list_display = ('original_name', 'corrected_name', 'submitted_at', 'approved')
    list_filter = ('approved', 'submitted_at')
    actions = ['approve_corrections']
    
    def approve_corrections(self, request, queryset):
        for correction in queryset:
            correction.approved = True
            correction.save()
        self.message_user(request, f"{queryset.count()} corrections were approved.")
    approve_corrections.short_description = "Approve selected corrections"

@admin.register(AddMember)
class AddMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'fathername', 'grandfathername')
    search_fields = ('name', 'fathername', 'grandfathername')

@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'submitted_at')
    search_fields = ('name', 'email', 'message')
    list_filter = ('submitted_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'father_name', 'phone', 'email_verified')
    search_fields = ('user__username', 'name', 'father_name', 'phone')
    list_filter = ('email_verified', 'is_blood_donor')

@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'blood_group', 'request_type', 'urgency', 'created_at')
    search_fields = ('name', 'phone')
    list_filter = ('blood_group', 'request_type', 'urgency', 'created_at')

@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'is_approved')
    search_fields = ('title', 'description', 'user__username')
    list_filter = ('is_approved', 'created_at')
    actions = ['approve_albums', 'unapprove_albums']
    
    def approve_albums(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} albums were approved.")
    approve_albums.short_description = "Approve selected albums"
    
    def unapprove_albums(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} albums were unapproved.")
    unapprove_albums.short_description = "Unapprove selected albums"

@admin.register(AlbumPhoto)
class AlbumPhotoAdmin(admin.ModelAdmin):
    list_display = ('album', 'caption', 'uploaded_at')
    search_fields = ('album__title', 'caption')
    list_filter = ('uploaded_at',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'user', 'created_at', 'is_approved')
    search_fields = ('title', 'content', 'user__username')
    list_filter = ('category', 'is_approved', 'created_at')
    actions = ['approve_posts', 'unapprove_posts']
    
    def approve_posts(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} posts were approved.")
    approve_posts.short_description = "Approve selected posts"
    
    def unapprove_posts(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} posts were unapproved.")
    unapprove_posts.short_description = "Unapprove selected posts"