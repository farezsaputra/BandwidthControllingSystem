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
    ominlimitup = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder" : "Maximum Shared Upload"
            }
        )
    ) 

    ominlimitdown = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder" : "Maximum Shared Download"
            }
        )
    )

    omaxlimitup = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder" : "Maximum Dedicated Upload"
            }
        )
    )

    omaxlimitdown = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder" : "Maximum Dedicated Download"
            }
        )
    )
    class Meta(object):
        model = configuration
        fields = "__all__"

class ForecastForm(ModelForm):
    data_date = forms.DateField()
    class Meta(object):
        model = dataset
        fields = "__all__"

class ControlForm(ModelForm):
    status = forms.BooleanField()
    class Meta(object):
        model = toogle
        fields = ['is_working']