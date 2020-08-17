from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from mikrotik.models import *
from .views import *
from django.forms import ModelForm

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

class ConfigForm(ModelForm): 
    class Meta(object):
        model = configuration
        fields = "__all__"


class ControlForm(ModelForm):
    status = forms.BooleanField()
    class Meta(object):
        model = toogle
        fields = ['is_working']