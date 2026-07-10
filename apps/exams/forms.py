from django import forms

from .models import SessionExamen, Inscription, AffectationJury, AnneeSportive, TarifExamen, Rubrique, RubriqueGrade, OptionExamen, ModeleMatricule, ParametresExamen
from apps.practitioners.models import Grade


class AnneeSportiveForm(forms.ModelForm):
    class Meta:
        model  = AnneeSportive
        fields = ['libelle', 'date_debut', 'date_fin', 'statut']
        widgets = {
            'libelle':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : 2025-2026'}),
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'statut':     forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'libelle':    'Libellé',
            'date_debut': 'Date de début',
            'date_fin':   'Date de fin',
            'statut':     'Statut',
        }


class SessionExamenForm(forms.ModelForm):
    class Meta:
        model = SessionExamen
        fields = [
            'annee_sportive', 'titre', 'date_examen', 'lieu',
            'date_ouverture_inscriptions', 'date_cloture_inscriptions',
            'date_limite_paiement',
        ]
        widgets = {
            'annee_sportive':              forms.Select(attrs={'class': 'form-select'}),
            'titre':                       forms.TextInput(attrs={'class': 'form-control'}),
            'lieu':                        forms.TextInput(attrs={'class': 'form-control'}),
            'date_examen':                 forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_ouverture_inscriptions': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_cloture_inscriptions':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_limite_paiement':        forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'annee_sportive':              "Année sportive",
            'titre':                       "Titre de la session",
            'lieu':                        "Lieu",
            'date_examen':                 "Date de l'examen",
            'date_ouverture_inscriptions': "Ouverture des inscriptions",
            'date_cloture_inscriptions':   "Clôture des inscriptions",
            'date_limite_paiement':        "Date limite de paiement des droits d'examen",
        }

    def __init__(self, *args, ligue=None, **kwargs):
        super().__init__(*args, **kwargs)
        if ligue:
            self.fields['annee_sportive'].queryset = AnneeSportive.objects.filter(
                ligue=ligue, statut='ACTIVE'
            )


class MultiInscriptionForm(forms.Form):
    """Formulaire multi-sélection pour inscrire plusieurs pratiquants en une fois."""
    grade_vise  = forms.ModelChoiceField(
        queryset=Grade.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_grade_vise'}),
        label="Grade visé",
        empty_label="— Choisir un grade visé —",
    )
    option = forms.ModelChoiceField(
        queryset=OptionExamen.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
        label="Option / Style",
        empty_label="— Choisir une option —",
        required=True,
    )
    pratiquants = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        label="Pratiquants à inscrire",
        required=False,
    )

    def __init__(self, *args, club=None, session=None, ligue=None, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.practitioners.models import Pratiquant
        self._session = session
        if club and session:
            deja_inscrits = Inscription.objects.filter(session=session).values_list('pratiquant_id', flat=True)
            self.fields['pratiquants'].queryset = (
                club.pratiquants.filter(actif=True)
                .exclude(pk__in=deja_inscrits)
                .select_related('grade_actuel')
                .order_by('nom', 'prenom')
            )
        else:
            self.fields['pratiquants'].queryset = Pratiquant.objects.none()

        if ligue:
            self.fields['grade_vise'].queryset = Grade.objects.filter(ligue=ligue, actif=True).order_by('id_grade')
            self.fields['option'].queryset = OptionExamen.objects.filter(ligue=ligue, actif=True)
        elif club:
            self.fields['grade_vise'].queryset = Grade.objects.filter(ligue=club.ligue, actif=True).order_by('id_grade')
            self.fields['option'].queryset = OptionExamen.objects.filter(ligue=club.ligue, actif=True)

    def clean(self):
        cleaned_data = super().clean()
        grade_vise  = cleaned_data.get('grade_vise')
        option      = cleaned_data.get('option')
        pratiquants = cleaned_data.get('pratiquants')
        if not grade_vise:
            raise forms.ValidationError("Veuillez choisir un grade visé.")
        if not option:
            raise forms.ValidationError("Veuillez choisir une option.")
        if not pratiquants:
            raise forms.ValidationError("Cochez au moins un pratiquant à inscrire.")
        # Validation : chaque pratiquant doit avoir exactement le grade précédent
        id_requis = grade_vise.id_grade - 1
        invalides = []
        for p in pratiquants:
            id_actuel = p.grade_actuel.id_grade if p.grade_actuel else 0
            if id_actuel != id_requis:
                invalides.append(f"{p.nom} {p.prenom}")
        if invalides:
            raise forms.ValidationError(
                f"Ces pratiquants n'ont pas le grade requis pour viser « {grade_vise} » : "
                + ", ".join(invalides)
            )
        return cleaned_data


class TarifExamenForm(forms.ModelForm):
    class Meta:
        model  = TarifExamen
        fields = ['grade', 'montant']
        widgets = {
            'grade':   forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex : 5000', 'min': '0', 'step': '100'}),
        }
        labels = {
            'grade':   'Grade visé',
            'montant': 'Montant (FCFA)',
        }

    def __init__(self, *args, ligue=None, annee=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._annee = annee
        if ligue:
            self.fields['grade'].queryset = Grade.objects.filter(ligue=ligue, actif=True).order_by('id_grade')
        else:
            self.fields['grade'].queryset = Grade.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        grade = cleaned_data.get('grade')
        if grade and self._annee:
            qs = TarifExamen.objects.filter(annee_sportive=self._annee, grade=grade)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"Un tarif existe déjà pour le grade « {grade.nom} » cette année. Modifiez-le directement."
                )
        return cleaned_data


class OptionExamenForm(forms.ModelForm):
    class Meta:
        model  = OptionExamen
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Shaolin, Wu Dang…'}),
        }
        labels = {'nom': "Nom de l'option"}


class ParametresExamenForm(forms.ModelForm):
    class Meta:
        model  = ParametresExamen
        fields = ['pourcentage_ligue']
        widgets = {
            'pourcentage_ligue': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0', 'max': '100', 'step': '0.5',
                'placeholder': 'Ex : 25',
            }),
        }
        labels = {'pourcentage_ligue': 'Pourcentage reversé à la ligue (%)'}

    def clean_pourcentage_ligue(self):
        val = self.cleaned_data['pourcentage_ligue']
        if val < 0 or val > 100:
            raise forms.ValidationError("Le pourcentage doit être entre 0 et 100.")
        return val


class ModeleMatriculeForm(forms.ModelForm):
    class Meta:
        model  = ModeleMatricule
        fields = ['prefixe']
        widgets = {
            'prefixe': forms.TextInput(attrs={
                'class': 'form-control text-uppercase',
                'placeholder': 'Ex : LK',
                'maxlength': '10',
                'style': 'letter-spacing:2px; font-weight:bold;',
            }),
        }
        labels = {'prefixe': 'Préfixe (sigle de la ligue)'}

    def clean_prefixe(self):
        return self.cleaned_data['prefixe'].upper().strip()


class RubriqueForm(forms.ModelForm):
    class Meta:
        model  = Rubrique
        fields = ['nom', 'description']
        widgets = {
            'nom':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Kata, Combat Sanda…'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description facultative'}),
        }
        labels = {
            'nom':         'Nom de la rubrique',
            'description': 'Description',
        }


class RubriqueGradeForm(forms.ModelForm):
    class Meta:
        model  = RubriqueGrade
        fields = ['grade', 'coefficient', 'note_minimale']
        widgets = {
            'grade':         forms.Select(attrs={'class': 'form-select'}),
            'coefficient':   forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '10'}),
            'note_minimale': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '5', 'step': '0.25'}),
        }
        labels = {
            'grade':         'Grade concerné',
            'coefficient':   'Coefficient',
            'note_minimale': 'Note minimale /5',
        }

    def __init__(self, *args, ligue=None, rubrique=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._rubrique = rubrique
        if ligue:
            deja = RubriqueGrade.objects.filter(rubrique=rubrique).values_list('grade_id', flat=True) if rubrique else []
            if self.instance and self.instance.pk:
                deja = [g for g in deja if g != self.instance.grade_id]
            self.fields['grade'].queryset = (
                Grade.objects.filter(ligue=ligue, actif=True)
                .exclude(pk__in=deja)
                .order_by('id_grade')
            )
        else:
            self.fields['grade'].queryset = Grade.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        grade = cleaned_data.get('grade')
        if grade and self._rubrique:
            qs = RubriqueGrade.objects.filter(rubrique=self._rubrique, grade=grade)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"Cette rubrique est déjà configurée pour le grade « {grade.nom} »."
                )
        return cleaned_data


class AffectationJuryForm(forms.ModelForm):
    class Meta:
        model = AffectationJury
        fields = ['jury']
        widgets = {
            'jury': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'jury': "Membre du jury",
        }

    def __init__(self, *args, session=None, ligue=None, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.accounts.models import Role
        if ligue and session:
            deja_affectes = AffectationJury.objects.filter(session=session).values_list('jury_id', flat=True)
            self.fields['jury'].queryset = (
                ligue.utilisateurs
                .filter(roles__nom_role=Role.JURY)
                .exclude(pk__in=deja_affectes)
                .distinct()
            )
        else:
            self.fields['jury'].queryset = self.fields['jury'].queryset.none()
