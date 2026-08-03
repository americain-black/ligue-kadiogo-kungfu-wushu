from django import forms
from .models import Actualite, Document


class ActualiteForm(forms.ModelForm):
    class Meta:
        model = Actualite
        fields = ['titre', 'contenu', 'image']
        widgets = {
            'titre':   forms.TextInput(attrs={'class': 'form-control'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'image':   forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'titre':   'Titre',
            'contenu': 'Contenu',
            'image':   'Image (facultatif)',
        }


class RejetActualiteForm(forms.Form):
    motif = forms.CharField(
        label='Motif du rejet',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True,
    )


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['titre', 'type_document', 'fichier', 'est_public']
        widgets = {
            'titre':         forms.TextInput(attrs={'class': 'form-control'}),
            'type_document': forms.Select(attrs={'class': 'form-select'}),
            'fichier':       forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'est_public':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'titre':         'Titre',
            'type_document': 'Type de document',
            'fichier':       'Fichier',
            'est_public':    'Document public (visible sans connexion)',
        }
