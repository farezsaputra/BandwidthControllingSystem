from django import forms

class AuthForm(forms.Form):
    address = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Alamat IP Router",                
                "class": "form-control",
                'autocomplete': 'off'
            }
        ))
    port = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Port SSH",                
                "class": "form-control",
                'autocomplete': 'off'
            }
        ))
    router = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Username Router",                
                "class": "form-control",
                'autocomplete': 'off'
            }
        ))
    sandi = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder" : "Password Router",                
                "class": "form-control",
                'autocomplete': 'off'
            }
        ))
    community = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Community SNMP",                
                "class": "form-control",
                'autocomplete': 'off'
            }
        ))

class PrintForm(forms.Form):
    nama = forms.CharField(
        widget=forms.HiddenInput(
            attrs={                
                "class": "form-control",
                'autocomplete': 'off'
            }
        )
    )
    bulan = forms.CharField(
        widget=forms.HiddenInput(
            attrs={                
                "class": "form-control",
                'autocomplete': 'off'
            }
        )
    )
    upload = forms.CharField(
        widget=forms.HiddenInput(
            attrs={                
                "class": "form-control",
                'autocomplete': 'off'
            }
        )
    )
    download = forms.CharField(
        widget=forms.HiddenInput(
            attrs={                
                "class": "form-control",
                'autocomplete': 'off'
            }
        )
    )
    langganan = forms.CharField(
        widget=forms.HiddenInput(
            attrs={                
                "class": "form-control",
                'autocomplete': 'off'
            }
        )
    )
    biaya = forms.CharField(
        widget=forms.HiddenInput(
            attrs={                
                "class": "form-control",
                'autocomplete': 'off'
            }
        )
    )