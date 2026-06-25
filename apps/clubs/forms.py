from django import forms
from .models import Club, DemandeAffiliation, VoletOrganigrammeClub, MembreOrganigrammeClub


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            'nom_club', 'sigle_club', 'localite',
            'adresse', 'telephone', 'email', 'statut_club',
        ]
        widgets = {
            'nom_club':   forms.TextInput(attrs={'class': 'form-control'}),
            'sigle_club': forms.TextInput(attrs={'class': 'form-control'}),
            'localite':   forms.TextInput(attrs={'class': 'form-control'}),
            'adresse':    forms.TextInput(attrs={'class': 'form-control'}),
            'telephone':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'statut_club': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nom_club':   'Nom du club',
            'sigle_club': 'Sigle',
            'localite':   'Localité',
            'adresse':    'Adresse',
            'telephone':  'Téléphone',
            'email':      'Email',
            'statut_club': 'Statut',
        }


class RejetDemandeForm(forms.Form):
    motif = forms.CharField(
        label='Motif du rejet',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True,
    )


class VoletOrganigrammeClubForm(forms.ModelForm):
    class Meta:
        model  = VoletOrganigrammeClub
        fields = ['nom_volet']
        widgets = {
            'nom_volet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Bureau Exécutif, Encadrement Technique...',
            }),
        }
        labels = {'nom_volet': 'Nom du volet'}


class MembreOrganigrammeClubForm(forms.ModelForm):
    class Meta:
        model  = MembreOrganigrammeClub
        fields = ['nom', 'prenom', 'contact', 'fonction', 'actif']
        widgets = {
            'nom':      forms.TextInput(attrs={'class': 'form-control'}),
            'prenom':   forms.TextInput(attrs={'class': 'form-control'}),
            'contact':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone ou email'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Président, DT...'}),
            'actif':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nom':      'Nom',
            'prenom':   'Prénom',
            'contact':  'Contact',
            'fonction': 'Fonction',
            'actif':    'Membre actif',
        }
