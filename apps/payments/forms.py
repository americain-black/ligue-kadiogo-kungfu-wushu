from django import forms
from .models import PaiementExamen


class PaiementExamenForm(forms.ModelForm):
    class Meta:
        model = PaiementExamen
        fields = ['montant_paye', 'reference', 'fichier_preuve']
        widgets = {
            'montant_paye':   forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0',
            }),
            'reference':      forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : OM-12345678, MM-87654321, n° reçu…',
            }),
            'fichier_preuve': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
        }
        labels = {
            'montant_paye':   "Montant payé (FCFA)",
            'reference':      "Référence / N° de reçu",
            'fichier_preuve': "Fichier preuve (PDF, JPG, PNG)",
        }


class RejetPaiementForm(forms.Form):
    motif = forms.CharField(
        label="Motif du rejet",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True,
    )
