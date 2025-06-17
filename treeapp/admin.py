from django.contrib import admin
from .models import FamilyMember, Correction, AddMember, HelpRequest, UserProfile, BloodRequest, Album, AlbumPhoto, Post, CustomNotification, Donation, CommitteeMember, RecentDonation
from django.utils.html import format_html

@admin.register(CommitteeMember)
class CommitteeMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'designation', 'picture_tag')
    search_fields = ('name', 'designation')
    readonly_fields = ('picture_tag',)

    def picture_tag(self, obj):
        if obj.picture:
            return format_html('<img src="{}" style="max-height:150px; max-width:150px;"/>', obj.picture.url)
        return "No Image"
    picture_tag.short_description = 'Picture'

@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'date_of_birth_display', 'year_of_birth', 'year_of_death')
    search_fields = ('name',)
    list_filter = ('year_of_birth', 'year_of_death')

    def date_of_birth_display(self, obj):
        if obj.date_of_birth:
            return obj.date_of_birth.strftime('%d/%m/%Y')
        return "-"
    date_of_birth_display.short_description = 'Date of Birth'

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
    list_display = ('title', 'category', 'user', 'created_at', 'is_approved', 'image_tag')
    search_fields = ('title', 'content', 'user__username')
    list_filter = ('category', 'is_approved', 'created_at')
    actions = ['approve_posts', 'unapprove_posts']
    readonly_fields = ['image_tag']
    
    def approve_posts(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} posts were approved.")
    approve_posts.short_description = "Approve selected posts"
    
    def unapprove_posts(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} posts were unapproved.")
    unapprove_posts.short_description = "Unapprove selected posts"

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:100px;"/>', obj.image.url)
        return "-"
    image_tag.short_description = 'Image'

@admin.register(CustomNotification)
class CustomNotificationAdmin(admin.ModelAdmin):
    list_display = ('message_preview', 'is_active', 'created_at', 'created_by')
    list_filter = ('is_active', 'created_at')
    search_fields = ('message', 'created_by__username')
    readonly_fields = ('created_at',)
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'donation_date', 'transaction_id', 'created_at')
    list_filter = ('donation_date', 'created_at')
    search_fields = ('name', 'transaction_id')
    ordering = ('-donation_date', '-created_at')
    readonly_fields = ('created_at',)

@admin.register(RecentDonation)
class RecentDonationAdmin(admin.ModelAdmin):
    list_display = ('user', 'donation_date', 'donation_location', 'created_at')
    list_filter = ('donation_date', 'created_at')
    search_fields = ('user__username', 'donation_location', 'donation_notes')
    ordering = ('-donation_date', '-created_at')
    readonly_fields = ('created_at',)