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
    othreshold = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder" : "Threshold"
            }
        )
    )

    ominlimitup = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder" : "Minimum Upload"

            }
        )
    ) 

    ominlimitdown = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder" : "Minimum Download"
            }
        )
    )

    omaxlimitup = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder" : "Maximum Upload"
            }
        )
    )

    omaxlimitdown = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder" : "Maximum Download"
            }
        )
    )
    class Meta(object):
        model = configuration
        fields = "__all__"