from django import forms
from .models import AddMember, HelpRequest, FamilyMember, Correction, BloodRequest, Album, AlbumPhoto, Post
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

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

class RegisterForm(UserCreationForm):
    BLOOD_GROUP_CHOICES = [
        ('', 'Select Blood Group'),
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
        ('', 'Select Gender'),
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your full name', 'autofocus': 'autofocus'})
    )
    father_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your father\'s name'})
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address'})
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number'})
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    blood_group = forms.ChoiceField(
        choices=BLOOD_GROUP_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_blood_donor = forms.BooleanField(
        required=False,
        initial=False,
        label='I am willing to donate blood'
    )
    
    class Meta:
        model = User
        fields = ['name', 'father_name', 'username', 'email', 'phone', 'gender', 'date_of_birth', 'blood_group', 'is_blood_donor', 'password1', 'password2']
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

class FamilyMemberForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Date of Birth'
    )
    year_of_birth = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}),
        label='Year of Birth (if full date not available)'
    )

    class Meta:
        model = FamilyMember
        fields = ['name', 'photo', 'date_of_birth', 'year_of_birth', 'year_of_death']

class CorrectionForm(forms.ModelForm):
    class Meta:
        model = Correction
        fields = ['original_name', 'corrected_name']
        widgets = {
            'original_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Original Name'}),
            'corrected_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Corrected Name'}),
        }

class BloodDonorForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = ['name', 'phone', 'blood_group', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Phone Number'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Your Address (optional)'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.request_type = 'donate'

class BloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = ['name', 'phone', 'blood_group', 'urgency', 'needed_where', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Phone Number'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'urgency': forms.Select(attrs={'class': 'form-control'}),
            'needed_where': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hospital/Location where blood is needed'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Your Address (optional)'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.request_type = 'need'

# New forms for Album, AlbumPhoto, and Post
class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Album Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Album Description'}),
        }

class AlbumPhotoForm(forms.ModelForm):
    class Meta:
        model = AlbumPhoto
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Photo Caption'}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Post Title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Post Content'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }