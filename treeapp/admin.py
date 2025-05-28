from django.contrib import admin
from .models import FamilyMember, NameSuggestion, Correction

@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent')
    search_fields = ('name',)

# @admin.register(NameSuggestion)
# class NameSuggestionAdmin(admin.ModelAdmin):
#     list_display = ('id', 'member', 'suggestion', 'approved')
#     list_editable = ('approved',)
#     list_filter = ('approved',)

    



@admin.register(Correction)
class CorrectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_name', 'corrected_name', 'approved', 'submitted_at')
    list_editable = ('approved',)
    list_filter = ('approved',)
    search_fields = ('original_name', 'corrected_name')

    


    from django.contrib import admin
from .models import AddMember

@admin.register(AddMember)
class AddMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'fathername', 'grandfathername')
    search_fields = ('name', 'fathername', 'grandfathername')

from django.contrib import admin
from .models import HelpRequest

@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "submitted_at")
    search_fields = ("name", "email", "phone", "message")
    list_filter = ("submitted_at",)
    readonly_fields = ("submitted_at",)