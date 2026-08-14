# pyrefly: ignore [missing-import]
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
            'nom_club', 'sigle_club', 'logo', 'code_club', 'nom_fondateur',
            'numero_recepisse', 'date_delivrance_recepisse', 'loi_reglementation', 'date_expiration_recepisse',
            'description', 'localite', 'adresse', 'telephone', 'email',
            'latitude', 'longitude', 'statut_club', 'utilisateur',
        ]
        widgets = {
            'nom_club':                  forms.TextInput(attrs={'class': 'form-control'}),
            'sigle_club':                forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CKW'}),
            'logo':                      forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'code_club':                 forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CL01 (Généré auto si vide)'}),
            'nom_fondateur':             forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Maître Koné Souleymane'}),
            'numero_recepisse':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: N° 2024-22/MSJE/RCEN/DRSL-CEN/SRRIS'}),
            'date_delivrance_recepisse': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_expiration_recepisse': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'loi_reglementation':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Loi N° 064-2015/CNT'}),
            'description':               forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Présentation du club, horaires des entraînements, styles enseignés...'}),
            'localite':                  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Ouagadougou, Secteur 15'}),
            'adresse':                   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Rue 14.25, Porte 102'}),
            'telephone':                 forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: +226 70 00 00 00'}),
            'email':                     forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ex: club@kadiogo-wushu.bf'}),
            'latitude':                  forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Ex: 12.3714'}),
            'longitude':                 forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Ex: -1.5197'}),
            'statut_club':               forms.Select(attrs={'class': 'form-select'}),
            'utilisateur':               forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nom_club':                  'Nom complet du club',
            'sigle_club':                'Sigle du club (ex: CKW)',
            'logo':                      'Logo officiel du club',
            'code_club':                 'Code unique du club (ex: CL01)',
            'nom_fondateur':             'Maître du club',
            'numero_recepisse':          'Numéro du récépissé d\'existence',
            'date_delivrance_recepisse': 'Date de délivrance du récépissé',
            'date_expiration_recepisse': 'Date d\'expiration du récépissé (Optionnel)',
            'loi_reglementation':        'Loi / Texte réglementaire',
            'description':               'Description / Présentation du club',
            'localite':                  'Localité',
            'adresse':                   'Adresse physique',
            'telephone':                 'Téléphone de contact',
            'email':                     'Adresse email',
            'latitude':                  'Latitude GPS',
            'longitude':                 'Longitude GPS',
            'statut_club':               'Statut d\'affiliation',
            'utilisateur':               'Gestionnaire du club',
        }
        help_texts = {
            'code_club':                 "Code unique du club (ex : CL01, CL02...). Généré automatiquement si vous le laissez vide.",
            'nom_fondateur':             "Nom complet du Maître principal du club (utilisé pour les bulletins et l'annuaire).",
            'description':               "Texte de présentation affiché sur la fiche du club dans l'annuaire public.",
        }

    def clean_telephone(self):
        from apps.accounts.forms import normaliser_telephone
        tel = self.cleaned_data.get('telephone')
        return normaliser_telephone(tel)

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


class ModeleAttestationForm(forms.ModelForm):
    class Meta:
        model  = ParametresAffiliation
        fields = [
            'attestation_pays', 'attestation_devise', 'attestation_sigle_ligue', 'attestation_sous_titre_ligue',
            'attestation_prefixe_enregistrement', 'attestation_titre',
            'attestation_texte_introduction', 'attestation_texte_conclusion',
            'attestation_titre_signataire', 'attestation_nom_signataire',
            'attestation_texte_sceau', 'attestation_ville_delivrance',
        ]
        widgets = {
            'attestation_pays': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: BURKINA FASO"}),
            'attestation_devise': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: Unité - Progrès - Justice"}),
            'attestation_sigle_ligue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: LKKFW"}),
            'attestation_sous_titre_ligue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: Ligue du Kadiogo de Kung-Fu Wushu"}),
            'attestation_prefixe_enregistrement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: N° d'enregistrement :"}),
            'attestation_titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: ATTESTATION D'AFFILIATION"}),
            'attestation_texte_introduction': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': "Texte d'introduction"}),
            'attestation_texte_conclusion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': "Texte de conclusion"}),
            'attestation_titre_signataire': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: Pour le Bureau Exécutif, Le Président de la Ligue"}),
            'attestation_nom_signataire': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: Nom du Président ou signataire"}),
            'attestation_texte_sceau': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: SCEAU OFFICIEL DE LA LIGUE"}),
            'attestation_ville_delivrance': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: Fait à Ouagadougou, le"}),
        }
        labels = {
            'attestation_pays': "Nom du Pays / En-tête supérieur",
            'attestation_devise': "Devise nationale / Slogan",
            'attestation_sigle_ligue': "Sigle / Acronyme de la Ligue (ex: LKKFW)",
            'attestation_sous_titre_ligue': "Nom complet de la Ligue dans l'en-tête",
            'attestation_prefixe_enregistrement': "Intitulé du N° d'enregistrement",
            'attestation_titre': "Titre principal du document",
            'attestation_texte_introduction': "Formule de certification (Introduction)",
            'attestation_texte_conclusion': "Paragraphe de conclusion (Droits accordés)",
            'attestation_titre_signataire': "Titre officiel du signataire",
            'attestation_nom_signataire': "Nom / Qualité du signataire",
            'attestation_texte_sceau': "Texte gravé sur le tampon / sceau officiel",
            'attestation_ville_delivrance': "Formule du lieu de délivrance",
        }


class ParametresAffiliationForm(forms.ModelForm):
    class Meta:
        model  = ParametresAffiliation
        fields = ['montant_frais_affiliation', 'exiger_recepisse_valide', 'duree_validite_recepisse_ans']
        widgets = {
            'montant_frais_affiliation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0', 'step': '1',
                'placeholder': 'Ex : 15000',
            }),
            'exiger_recepisse_valide': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'duree_validite_recepisse_ans': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1', 'max': '10',
                'placeholder': 'Ex : 3',
            }),
        }
        labels = {
            'montant_frais_affiliation': "Montant des frais d'affiliation (FCFA)",
            'exiger_recepisse_valide': "Exiger obligatoirement les détails du récépissé lors des affiliations",
            'duree_validite_recepisse_ans': "Durée de validité par défaut du récépissé (en années)",
        }

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
        fields = ['nom', 'prenom', 'contact', 'fonction', 'ordre', 'date_debut_fonction', 'actif']
        widgets = {
            'nom':                 forms.TextInput(attrs={'class': 'form-control'}),
            'prenom':              forms.TextInput(attrs={'class': 'form-control'}),
            'contact':             forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone ou email'}),
            'fonction':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Président, DT...'}),
            'ordre':               forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': '1, 2, 3...'}),
            'date_debut_fonction': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actif':               forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nom':                 'Nom',
            'prenom':              'Prénom',
            'contact':             'Contact',
            'fonction':            'Fonction',
            'ordre':               'Ligne / Niveau hiérarchique (1 = Ligne 1, 2 = Ligne 2...)',
            'date_debut_fonction': 'Date de début de fonction',
            'actif':               'Membre actif',
        }


class ClubProfilForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            'logo', 'nom_fondateur', 'numero_recepisse', 'date_delivrance_recepisse',
            'loi_reglementation', 'date_expiration_recepisse', 'description', 'localite', 'adresse',
            'telephone', 'email', 'latitude', 'longitude',
        ]
        widgets = {
            'logo':                      forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'nom_fondateur':             forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Maître Koné Souleymane'}),
            'numero_recepisse':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: N° 2024-22/MSJE/RCEN/DRSL-CEN/SRRIS'}),
            'date_delivrance_recepisse': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_expiration_recepisse': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'loi_reglementation':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Loi N° 064-2015/CNT'}),
            'description':               forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Présentation du club, horaires des entraînements, styles enseignés...'}),
            'localite':                  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Ouagadougou, Secteur 15'}),
            'adresse':                   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Rue 14.25, Porte 102'}),
            'telephone':                 forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: +226 70 00 00 00'}),
            'email':                     forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ex: club@kadiogo-wushu.bf'}),
            'latitude':                  forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Ex: 12.3714'}),
            'longitude':                 forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Ex: -1.5197'}),
        }
        labels = {
            'logo':                      'Logo officiel du club',
            'nom_fondateur':             'Maître du club',
            'numero_recepisse':          'Numéro du récépissé d\'existence',
            'date_delivrance_recepisse': 'Date de délivrance du récépissé',
            'date_expiration_recepisse': 'Date d\'expiration du récépissé (Optionnel)',
            'loi_reglementation':        'Loi / Texte réglementaire',
            'description':               'Description / Présentation du club',
            'localite':                  'Localité',
            'adresse':                   'Adresse physique',
            'telephone':                 'Téléphone de contact du club',
            'email':                     'Adresse email du club',
            'latitude':                  'Latitude GPS',
            'longitude':                 'Longitude GPS',
        }
        help_texts = {
            'description': "Cette description sera affichée sur la fiche de votre club dans l'annuaire public.",
        }
