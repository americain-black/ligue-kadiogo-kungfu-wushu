from django import forms
from .models import (
    Club, DemandeAffiliation, PieceJustificativeAffiliation,
    ParametresAffiliation, VoletOrganigrammeClub, MembreOrganigrammeClub,
)
from apps.accounts.models import Utilisateur, Role


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            'nom_club', 'sigle_club', 'localite',
            'adresse', 'telephone', 'email', 'statut_club',
            'utilisateur',
        ]
        widgets = {
            'nom_club':    forms.TextInput(attrs={'class': 'form-control'}),
            'sigle_club':  forms.TextInput(attrs={'class': 'form-control'}),
            'localite':    forms.TextInput(attrs={'class': 'form-control'}),
            'adresse':     forms.TextInput(attrs={'class': 'form-control'}),
            'telephone':   forms.TextInput(attrs={'class': 'form-control'}),
            'email':       forms.EmailInput(attrs={'class': 'form-control'}),
            'statut_club': forms.Select(attrs={'class': 'form-select'}),
            'utilisateur': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nom_club':    'Nom du club',
            'sigle_club':  'Sigle',
            'localite':    'Localité',
            'adresse':     'Adresse',
            'telephone':   'Téléphone',
            'email':       'Email',
            'statut_club': 'Statut',
            'utilisateur': 'Gestionnaire du club',
        }

    def __init__(self, *args, ligue=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['utilisateur'].required = False
        self.fields['utilisateur'].empty_label = "— Aucun gestionnaire assigné —"

        if ligue:
            # Utilisateurs GEST_CLUB de cette ligue
            gest_club_qs = Utilisateur.objects.filter(
                ligue=ligue,
                roles__nom_role=Role.GEST_CLUB,
                statut_compte=True,
            ).distinct()

            # Exclure ceux qui gèrent déjà un autre club
            # (sauf le gestionnaire actuel de CE club)
            club_actuel_utilisateur_id = (
                self.instance.utilisateur_id if self.instance and self.instance.pk else None
            )
            deja_gestionnaires = (
                Club.objects.filter(utilisateur__isnull=False)
                .exclude(utilisateur_id=club_actuel_utilisateur_id)
                .values_list('utilisateur_id', flat=True)
            )
            gest_club_qs = gest_club_qs.exclude(pk__in=deja_gestionnaires)

            self.fields['utilisateur'].queryset = gest_club_qs
        else:
            self.fields['utilisateur'].queryset = Utilisateur.objects.none()


class ParametresAffiliationForm(forms.ModelForm):
    class Meta:
        model  = ParametresAffiliation
        fields = ['montant_frais_affiliation']
        widgets = {
            'montant_frais_affiliation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0', 'step': '1',
                'placeholder': 'Ex : 15000',
            }),
        }
        labels = {'montant_frais_affiliation': "Montant des frais d'affiliation (FCFA)"}

    def clean_montant_frais_affiliation(self):
        val = self.cleaned_data['montant_frais_affiliation']
        if val < 0:
            raise forms.ValidationError("Le montant ne peut pas être négatif.")
        return val


class PieceJustificativeAffiliationForm(forms.ModelForm):
    class Meta:
        model  = PieceJustificativeAffiliation
        fields = ['type_piece', 'fichier']
        widgets = {
            'type_piece': forms.Select(attrs={'class': 'form-select'}),
            'fichier':    forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
        }
        labels = {
            'type_piece': 'Type de document',
            'fichier':    'Fichier (PDF, JPG, PNG)',
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
        fields = ['nom', 'prenom', 'contact', 'fonction', 'date_debut_fonction', 'actif']
        widgets = {
            'nom':                 forms.TextInput(attrs={'class': 'form-control'}),
            'prenom':              forms.TextInput(attrs={'class': 'form-control'}),
            'contact':             forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone ou email'}),
            'fonction':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Président, DT...'}),
            'date_debut_fonction': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actif':               forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nom':                 'Nom',
            'prenom':              'Prénom',
            'contact':             'Contact',
            'fonction':            'Fonction',
            'date_debut_fonction': 'Date de début de fonction',
            'actif':               'Membre actif',
        }
