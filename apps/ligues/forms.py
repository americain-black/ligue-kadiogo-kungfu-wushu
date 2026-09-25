# pyrefly: ignore [missing-import]
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
            'nom_ligue':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'sigle':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'region':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'adresse_siege': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'email_contact': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'telephone':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'logo':          forms.FileInput(attrs={'class': 'form-control'}),
        }


class EditerInfosLigueForm(forms.ModelForm):
    class Meta:
        model = Ligue
        fields = [
            'nom_ligue', 'sigle', 'region', 'adresse_siege', 'email_contact', 'telephone', 'logo',
            'presentation_generale', 'historique', 'objectif_general', 'objectifs_specifiques',
            'vision', 'valeurs', 'mot_president', 'nom_president', 'photo_president',
            'titre_presentation', 'titre_mot_president', 'titre_organigramme',
            'titre_vision_missions', 'titre_contact', 'titre_hero_accueil', 'soustitre_hero_accueil', 'phrases_hero_accueil',
            'bulletin_header_gauche_ligne1', 'bulletin_header_gauche_ligne2',
            'bulletin_header_droite_ligne1', 'bulletin_header_droite_devise',
            'bulletin_signataire_titre', 'bulletin_signataire_nom', 'bulletin_signataire_grade',
            'bulletin_pied_legal', 'bulletin_mention_exemplaire', 'bulletin_prefixe_securite'
        ]
        widgets = {
            'nom_ligue':             forms.TextInput(attrs={'class': 'form-control'}),
            'sigle':                 forms.TextInput(attrs={'class': 'form-control'}),
            'region':                forms.TextInput(attrs={'class': 'form-control'}),
            'adresse_siege':         forms.TextInput(attrs={'class': 'form-control'}),
            'email_contact':         forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone':             forms.TextInput(attrs={'class': 'form-control'}),
            'logo':                  forms.FileInput(attrs={'class': 'form-control'}),
            'presentation_generale': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'historique':            forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'objectif_general':      forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'objectifs_specifiques': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'vision':                forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valeurs':               forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'mot_president':         forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'nom_president':         forms.TextInput(attrs={'class': 'form-control'}),
            'photo_president':       forms.FileInput(attrs={'class': 'form-control'}),
            'titre_presentation':    forms.TextInput(attrs={'class': 'form-control'}),
            'titre_mot_president':   forms.TextInput(attrs={'class': 'form-control'}),
            'titre_organigramme':    forms.TextInput(attrs={'class': 'form-control'}),
            'titre_vision_missions': forms.TextInput(attrs={'class': 'form-control'}),
            'titre_contact':         forms.TextInput(attrs={'class': 'form-control'}),
            'titre_hero_accueil':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(Optionnel)'}),
            'soustitre_hero_accueil': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': '(Optionnel)'}),
            'phrases_hero_accueil':  forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'bulletin_header_gauche_ligne1': forms.TextInput(attrs={'class': 'form-control'}),
            'bulletin_header_gauche_ligne2': forms.TextInput(attrs={'class': 'form-control'}),
            'bulletin_header_droite_ligne1': forms.TextInput(attrs={'class': 'form-control'}),
            'bulletin_header_droite_devise': forms.TextInput(attrs={'class': 'form-control'}),
            'bulletin_signataire_titre':     forms.TextInput(attrs={'class': 'form-control'}),
            'bulletin_signataire_nom':       forms.TextInput(attrs={'class': 'form-control'}),
            'bulletin_signataire_grade':     forms.TextInput(attrs={'class': 'form-control'}),
            'bulletin_pied_legal':           forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'bulletin_mention_exemplaire':   forms.TextInput(attrs={'class': 'form-control'}),
            'bulletin_prefixe_securite':     forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nom_ligue':             'Nom officiel de la Ligue',
            'sigle':                 'Sigle / Acronyme',
            'region':                'Région sportive',
            'adresse_siege':         'Adresse du Siège Social',
            'email_contact':         'Email de contact officiel',
            'telephone':             'Numéro(s) de téléphone',
            'logo':                  'Logo officiel de la Ligue (Optionnel)',
            'presentation_generale': 'Présentation Générale',
            'historique':            'Historique du Wushu dans la Région (Optionnel)',
            'objectif_general':      'Objectif Général',
            'objectifs_specifiques': 'Objectifs Spécifiques (Optionnel)',
            'vision':                'Vision Stratégique (Optionnel)',
            'valeurs':               'Valeurs Fondamentales (Optionnel)',
            'mot_president':         'Mot du Président / de la Présidente (Optionnel)',
            'nom_president':         'Nom & Titre du Président (Optionnel)',
            'photo_president':       'Photo officielle du Président (Optionnel)',
            'titre_presentation':    'Libellé du menu : Présentation (Optionnel)',
            'titre_mot_president':   'Libellé du menu : Mot du Président (Optionnel)',
            'titre_organigramme':    'Libellé du menu : Organigramme (Optionnel)',
            'titre_vision_missions': 'Libellé du menu : Vision & Missions (Optionnel)',
            'titre_contact':         'Libellé du menu : Contact (Optionnel)',
            'bulletin_header_gauche_ligne1': 'Bulletin — En-tête gauche (Fédération)',
            'bulletin_header_gauche_ligne2': 'Bulletin — En-tête gauche (Ligue)',
            'bulletin_header_droite_ligne1': 'Bulletin — En-tête droite (Pays)',
            'bulletin_header_droite_devise': 'Bulletin — En-tête droite (Devise)',
            'bulletin_signataire_titre':     'Bulletin — Titre du signataire',
            'bulletin_signataire_nom':       'Bulletin — Nom du signataire',
            'bulletin_signataire_grade':     'Bulletin — Grade du signataire',
            'bulletin_pied_legal':           'Bulletin — Pied de page légal et adresse',
            'bulletin_mention_exemplaire':   'Bulletin — Mention bas de page (Exemplaire unique)',
            'bulletin_prefixe_securite':     'Bulletin — Préfixe du Code de Sécurité',
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
        fields = ['nom', 'prenom', 'contact', 'fonction', 'ordre', 'date_debut_fonction', 'actif']
        widgets = {
            'nom':                 forms.TextInput(attrs={'class': 'form-control'}),
            'prenom':              forms.TextInput(attrs={'class': 'form-control'}),
            'contact':             forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone ou email'}),
            'fonction':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Président(e), Secrétaire, Entraîneur...'}),
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
