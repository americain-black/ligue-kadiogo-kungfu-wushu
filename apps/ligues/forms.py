from django import forms
from .models import Ligue


class LigueForm(forms.ModelForm):
    class Meta:
        model  = Ligue
        fields = [
            'nom_ligue', 'sigle', 'region', 'adresse_siege',
            'email_contact', 'telephone', 'logo',
            'nom_directeur_adm', 'nom_directeur_tech',
            'nom_secretaire', 'contact_secretaire',
        ]
        widgets = {
            'nom_ligue':       forms.TextInput(attrs={'class': 'form-control'}),
            'sigle':           forms.TextInput(attrs={'class': 'form-control'}),
            'region':          forms.TextInput(attrs={'class': 'form-control'}),
            'adresse_siege':   forms.TextInput(attrs={'class': 'form-control'}),
            'email_contact':   forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone':       forms.TextInput(attrs={'class': 'form-control'}),
            'logo':            forms.FileInput(attrs={'class': 'form-control'}),
            'nom_directeur_adm':  forms.TextInput(attrs={'class': 'form-control'}),
            'nom_directeur_tech': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_secretaire':     forms.TextInput(attrs={'class': 'form-control'}),
            'contact_secretaire': forms.TextInput(attrs={'class': 'form-control'}),
        }
