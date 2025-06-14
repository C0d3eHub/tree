from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

class FamilyMember(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    photo = models.ImageField(upload_to='family_photos/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    year_of_birth = models.PositiveIntegerField(null=True, blank=True)
    year_of_death = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    family_root = models.ForeignKey(FamilyMember, null=True, blank=True, on_delete=models.SET_NULL, related_name='root_for_users')
    last_child = models.ForeignKey(FamilyMember, null=True, blank=True, on_delete=models.SET_NULL, related_name='last_child_for_users')
    member_id = models.ForeignKey(FamilyMember, null=True, blank=True, on_delete=models.SET_NULL, related_name='member_id_for_users')
    name = models.CharField(max_length=100, blank=True, null=True)
    father_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    plain_password = models.CharField(max_length=100, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    is_blood_donor = models.BooleanField(default=False)
    hide_from_donor_list = models.BooleanField(default=False)
    picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    marital_status = models.CharField(max_length=20, choices=[('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widowed', 'Widowed')], blank=True, null=True)
    anniversary_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.user.username

class NameSuggestion(models.Model):
    member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE)
    suggestion = models.CharField(max_length=100)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.suggestion} for {self.member.name}"

class Correction(models.Model):
    original_name = models.CharField(max_length=255)
    corrected_name = models.CharField(max_length=255)
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)  # Added for admin approval

    def __str__(self):
        return f"{self.original_name} → {self.corrected_name}"
    class Meta:
        verbose_name = "Name Correction Request"
        verbose_name_plural = "Name Correction Requests"

# Signal to update FamilyMember when a Correction is approved
@receiver(post_save, sender=Correction)
def apply_correction(sender, instance, **kwargs):
    if instance.approved:
        try:
            member = FamilyMember.objects.get(name=instance.original_name)
            member.name = instance.corrected_name
            member.save()
        except FamilyMember.DoesNotExist:
            pass  # Optionally log this

class AddMember(models.Model):
    name = models.CharField(max_length=100)
    fathername = models.CharField(max_length=100)
    grandfathername = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Request to Add Member"
        verbose_name_plural = "Requests to Add Members"

class HelpRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"HelpRequest from {self.name} ({self.email})"
        
class BloodRequest(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    REQUEST_TYPE_CHOICES = [
        ('donate', 'Donate Blood'),
        ('need', 'Need Blood'),
    ]
    
    URGENCY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPE_CHOICES)
    address = models.TextField(blank=True, null=True)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, blank=True, null=True)
    needed_where = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_registered_user = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} - {self.blood_group} ({self.get_request_type_display()})"

# New models for user albums and posts
class Album(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

class AlbumPhoto(models.Model):
    album = models.ForeignKey(Album, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='album_photos/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Photo in {self.album.title}"

class Post(models.Model):
    CATEGORY_CHOICES = [
        ('news', 'News'),
        ('event', 'Event'),
        ('history', 'History'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    
    def __str__(self):
        return self.title

class CustomNotification(models.Model):
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification by {self.created_by.username} - {self.created_at.strftime('%Y-%m-%d')}"

class Donation(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100)
    donation_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ₹{self.amount} - {self.donation_date}"