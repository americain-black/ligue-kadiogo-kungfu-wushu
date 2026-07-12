from django import forms
from .models import PaiementExamen, PaiementAffiliation


class PaiementExamenForm(forms.ModelForm):
    class Meta:
        model = PaiementExamen
        fields = [
            'mode_paiement',
            'numero_expediteur',
            'numero_beneficiaire',
            'nom_payeur',
            'montant_paye',
            'reference',
            'fichier_preuve',
        ]
        widgets = {
            'mode_paiement':       forms.Select(attrs={'class': 'form-select', 'id': 'id_mode_paiement'}),
            'numero_expediteur':   forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : +226 70 00 00 00',
            }),
            'numero_beneficiaire': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : +226 70 00 00 00',
            }),
            'nom_payeur':          forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : Ouédraogo Salif',
            }),
            'montant_paye':        forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0',
            }),
            'reference':           forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : OM-12345678, MM-87654321…',
            }),
            'fichier_preuve':      forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
        }
        labels = {
            'mode_paiement':       "Mode de paiement",
            'numero_expediteur':   "Numéro expéditeur (optionnel)",
            'numero_beneficiaire': "Numéro bénéficiaire",
            'nom_payeur':          "Nom du payeur",
            'montant_paye':        "Montant payé (FCFA)",
            'reference':           "Référence / N° de transaction (dépôt mobile)",
            'fichier_preuve':      "Fichier preuve (PDF, JPG, PNG)",
        }

    def clean(self):
        cleaned = super().clean()
        mode    = cleaned.get('mode_paiement')
        if mode == 'DEPOT_MOBILE':
            if not cleaned.get('numero_beneficiaire', '').strip():
                self.add_error('numero_beneficiaire', "Requis pour un dépôt mobile.")
        if mode == 'ESPECES':
            if not cleaned.get('nom_payeur', '').strip():
                self.add_error('nom_payeur', "Indiquez le nom de la personne qui a payé.")
        return cleaned


class PaiementAffiliationForm(forms.ModelForm):
    class Meta:
        model = PaiementAffiliation
        fields = ['montant_paye', 'reference', 'fichier_preuve']
        widgets = {
            'montant_paye':   forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0',
            }),
            'reference':      forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : OM-12345678, MM-87654321…',
            }),
            'fichier_preuve': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
        }
        labels = {
            'montant_paye':   "Montant payé (FCFA)",
            'reference':      "Référence / N° de transaction",
            'fichier_preuve': "Fichier preuve (PDF, JPG, PNG)",
        }


class RejetPaiementForm(forms.Form):
    motif = forms.CharField(
        label="Motif du rejet",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True,
    )


class InsuffisantPaiementForm(forms.Form):
    motif = forms.CharField(
        label="Message au gestionnaire de club",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=True,
        help_text="Ce message sera envoyé au GC pour lui expliquer la situation.",
    )
