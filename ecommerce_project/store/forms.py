from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Order
from django.contrib.auth.models import User
import re

class CustomUserForm(UserCreationForm):
    #fullname=forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Enter Your Fullname'}))
    username=forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Enter Your Username'}))
    email=forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Enter Your Email Address'}))
    password1=forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Enter Your Password'}))
    password2=forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Confirm Password'}))
    class Meta:
        model=User
        fields=['username','email','password1','password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if not email.lower().endswith('@gmail.com'):
            raise forms.ValidationError("Only Gmail addresses are allowed.")
        
        username = email.split('@')[0]
        
        if len(re.findall(r'[a-zA-Z]', username)) < 3:
            raise forms.ValidationError("Email must contain at least 3 letters.")

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")

        
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")
        user.is_active = False  # 🔐 User must verify email to activate
        if commit:
            user.save()
        return user




class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'phone', 'address']