from django import forms
from .models import AddMember , HelpRequest

class AddMemberForm(forms.ModelForm):
    class Meta:
        model = AddMember
        fields = ['name', 'fathername', 'grandfathername']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name', 'class':'tree-input'}),
            'fathername': forms.TextInput(attrs={'placeholder': 'Father Name', 'class':'tree-input'}),
            'grandfathername': forms.TextInput(attrs={'placeholder': 'Grandfather Name', 'class':'tree-input'}),
        }


class HelpRequestForm(forms.ModelForm):
    class Meta:
        model = HelpRequest
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Phone (optional)'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Your Message'}),
        }
from django import forms
from .models import FamilyMember

class AddMultipleChildrenForm(forms.Form):
    parent = forms.ModelChoiceField(
        queryset=FamilyMember.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    child_1 = forms.CharField(label="Child 1", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Child Name'}))
    child_2 = forms.CharField(label="Child 2", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Child Name'}))
    child_3 = forms.CharField(label="Child 3", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Child Name'}))
    child_4 = forms.CharField(label="Child 4", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Child Name'}))
    child_5 = forms.CharField(label="Child 5", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Child Name'}))
    child_6 = forms.CharField(label="Child 6", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Child Name'}))
    child_7 = forms.CharField(label="Child 7", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Child Name'}))