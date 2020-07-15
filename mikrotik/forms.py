from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SetValueForm(forms.Form):
    upload = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Upload",                
                "class": "form-control"
            }
        ))
    download = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Download",                
                "class": "form-control"
            }
        ))

class SetValue(forms.Form):
    upload = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Upload",                
                "class": "form-control"
            }
        ))
    download = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Download",                
                "class": "form-control"
            }
        ))