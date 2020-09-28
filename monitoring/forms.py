from django import forms

class AuthForm(forms.Form):
    address = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Alamat IP Router",                
                "class": "form-control"
            }
        ))
    port = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Port SSH",                
                "class": "form-control"
            }
        ))
    router = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Username Router",                
                "class": "form-control"
            }
        ))
    sandi = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder" : "Password Router",                
                "class": "form-control"
            }
        ))
    community = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Community SNMP",                
                "class": "form-control"
            }
        ))