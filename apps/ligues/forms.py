from django import forms
from .models import Ligue, VoletOrganigramme, MembreOrganigramme


class LigueForm(forms.ModelForm):
    class Meta:
        model  = Ligue
        fields = [
            'nom_ligue', 'sigle', 'region',
            'adresse_siege', 'email_contact', 'telephone', 'logo',
        ]
        widgets = {
            'nom_ligue':     forms.TextInput(attrs={'class': 'form-control'}),
            'sigle':         forms.TextInput(attrs={'class': 'form-control'}),
            'region':        forms.TextInput(attrs={'class': 'form-control'}),
            'adresse_siege': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contact': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone':     forms.TextInput(attrs={'class': 'form-control'}),
            'logo':          forms.FileInput(attrs={'class': 'form-control'}),
        }


class VoletOrganigrammeForm(forms.ModelForm):
    class Meta:
        model  = VoletOrganigramme
        fields = ['nom_volet']
        widgets = {
            'nom_volet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Bureau Exécutif, Direction Technique...',
            }),
        }
        labels = {'nom_volet': 'Nom du volet'}


class MembreOrganigrammeForm(forms.ModelForm):
    class Meta:
        model  = MembreOrganigramme
        fields = ['nom', 'prenom', 'contact', 'fonction', 'actif']
        widgets = {
            'nom':      forms.TextInput(attrs={'class': 'form-control'}),
            'prenom':   forms.TextInput(attrs={'class': 'form-control'}),
            'contact':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone ou email'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Président, Trésorier...'}),
            'actif':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nom':      'Nom',
            'prenom':   'Prénom',
            'contact':  'Contact',
            'fonction': 'Fonction',
            'actif':    'Membre actif',
        }
