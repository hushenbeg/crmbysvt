from django import forms
from django.contrib.auth.forms import UserCreationForm
from crm.models import CustomUser  # Import your custom user model
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()  # ✅ This fetches your CustomUser model

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser  # Use your custom user model
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'profile_picture']

from .models import Profile  # Import your Profile model

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'phone', 'gender', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

# forms.py
from django import forms
from .models import CustomerData

class CustomerDataForm(forms.ModelForm):
    class Meta:
        model = CustomerData
        exclude = ['date'] 
        # fields = '__all__'  # or list specific fields like ['name', 'email', ...]


