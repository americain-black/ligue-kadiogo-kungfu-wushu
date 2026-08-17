from django import forms
from .models import Pratiquant, Grade, HistoriquePassageGrade


class PratiquantForm(forms.ModelForm):
    grade_actuel_nom = forms.ModelChoiceField(
        required=False,
        label='Grade actuel',
        queryset=Grade.objects.none(),
        empty_label='— Aucun grade —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model  = Pratiquant
        fields = ['nom', 'prenom', 'date_naissance', 'sexe', 'lieu_naissance',
                  'telephone', 'photo', 'bulletin_grade', 'actif']
        widgets = {
            'nom':            forms.TextInput(attrs={'class': 'form-control'}),
            'prenom':         forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe':           forms.Select(attrs={'class': 'form-select'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone':      forms.TextInput(attrs={'class': 'form-control'}),
            'photo':          forms.FileInput(attrs={'class': 'form-control'}),
            'bulletin_grade': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
            'actif':          forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nom':            'Nom',
            'prenom':         'Prénom',
            'date_naissance': 'Date de naissance',
            'sexe':           'Sexe',
            'lieu_naissance': 'Lieu de naissance',
            'telephone':      'Téléphone',
            'photo':          'Photo',
            'bulletin_grade': 'Bulletin / attestation de grade',
            'actif':          'Licencié actif',
        }

    def __init__(self, *args, ligue=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._ligue = ligue
        self.fields['bulletin_grade'].required = False
        if ligue:
            qs = Grade.objects.filter(ligue=ligue, actif=True).order_by('id_grade')
        else:
            qs = Grade.objects.filter(actif=True).order_by('id_grade')
        self.fields['grade_actuel_nom'].queryset = qs
        if self.instance and self.instance.pk and self.instance.grade_actuel:
            self.initial['grade_actuel_nom'] = self.instance.grade_actuel

    def clean(self):
        cleaned_data  = super().clean()
        grade_choisi  = cleaned_data.get('grade_actuel_nom')
        bulletin      = cleaned_data.get('bulletin_grade')
        # Bulletin requis si création ET grade id_grade >= 2
        # En modification, un bulletin déjà enregistré sur le licencié est accepté
        est_creation = not (self.instance and self.instance.pk)
        if grade_choisi and grade_choisi.id_grade >= 2:
            bulletin_existant = (
                self.instance and self.instance.pk and self.instance.bulletin_grade
            )
            if not bulletin and not bulletin_existant:
                self.add_error(
                    'bulletin_grade',
                    "Le bulletin / attestation du grade actuel est obligatoire "
                    f"pour un licencié de grade « {grade_choisi} »."
                )
        return cleaned_data

    def save(self, commit=True):
        pratiquant = super().save(commit=False)
        pratiquant.grade_actuel = self.cleaned_data.get('grade_actuel_nom')
        if commit:
            pratiquant.save()
        return pratiquant


class HistoriquePassageGradeForm(forms.ModelForm):
    class Meta:
        model = HistoriquePassageGrade
        fields = ['date_passage', 'grade_libelle', 'moyenne', 'rang', 'mention']
        widgets = {
            'date_passage': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'grade_libelle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: JAUNE, BLEUE, ROUGE...'}),
            'moyenne': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '20', 'placeholder': 'Ex: 14.50'}),
            'rang': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1er, 3 Ex, 5è...'}),
            'mention': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Bien, Passable...'}),
        }

