from django import forms
from django.contrib.auth.forms import AuthenticationForm


class NutriAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Nome de utilizador',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control input-form',
                'placeholder': 'O seu nome de utilizador',
                'autocomplete': 'username',
            }
        ),
    )
    password = forms.CharField(
        label='Palavra-passe',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control input-form',
                'placeholder': '••••••••',
                'autocomplete': 'current-password',
            }
        ),
    )
