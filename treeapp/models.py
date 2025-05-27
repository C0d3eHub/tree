from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class FamilyMember(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')

    def __str__(self):
        return self.name

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

from django.db import models
class HelpRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"HelpRequest from {self.name} ({self.email})"