# forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Region

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"placeholder":"username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder":"password"}))

class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['name', 'code']
        widgets = {
            "name": forms.TextInput(attrs={"placeholder":"Region name"}),
            "code": forms.TextInput(attrs={"placeholder":"Code (optional)"}),
        }

class CreateRMForm(forms.Form):
    region = forms.ModelChoiceField(queryset=Region.objects.all(), required=False, empty_label="Select region (optional)")
    manager_id = forms.CharField(max_length=50)
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class EditRMForm(forms.Form):
    region = forms.ModelChoiceField(queryset=Region.objects.all(), required=False, empty_label="Select region (optional)")
    manager_id = forms.CharField(max_length=50)
    username = forms.CharField(max_length=150)

class CreateEmployeeForm(forms.Form):
    regional_manager = forms.ModelChoiceField(queryset=None)  # set in view
    employee_id = forms.CharField(max_length=50)
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
