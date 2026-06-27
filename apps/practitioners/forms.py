from django import forms
from .models import Pratiquant, Grade


class PratiquantForm(forms.ModelForm):
    # Champ texte pour le grade : l'utilisateur tape le nom, on résout vers l'objet Grade
    grade_actuel_nom = forms.CharField(
        required=False,
        label='Grade actuel',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list':  'grades-datalist',
            'autocomplete': 'off',
            'placeholder': 'Ex : Blanc, Jaune, Vert, Bleu, Marron, Noir...',
        }),
    )

    class Meta:
        model  = Pratiquant
        fields = ['nom', 'prenom', 'date_naissance', 'sexe', 'lieu_naissance',
                  'telephone', 'photo', 'actif']
        widgets = {
            'nom':            forms.TextInput(attrs={'class': 'form-control'}),
            'prenom':         forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe':           forms.Select(attrs={'class': 'form-select'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone':      forms.TextInput(attrs={'class': 'form-control'}),
            'photo':          forms.FileInput(attrs={'class': 'form-control'}),
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
            'actif':          'Pratiquant actif',
        }

    def __init__(self, *args, ligue=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._ligue = ligue
        # Pré-remplir avec le grade actuel de l'instance si elle existe
        if self.instance and self.instance.pk and self.instance.grade_actuel:
            self.initial['grade_actuel_nom'] = self.instance.grade_actuel.nom

    def clean_grade_actuel_nom(self):
        nom = self.cleaned_data.get('grade_actuel_nom', '').strip()
        if not nom:
            return None
        qs = Grade.objects.filter(actif=True)
        if self._ligue:
            qs = qs.filter(ligue=self._ligue)
        grade = qs.filter(nom__iexact=nom).order_by('ordre').first()
        if grade:
            return grade
        noms_valides = ', '.join(qs.order_by('ordre').values_list('nom', flat=True))
        raise forms.ValidationError(
            f"Grade « {nom} » introuvable. Grades disponibles : {noms_valides or 'aucun grade créé pour cette ligue'}"
        )

    def save(self, commit=True):
        pratiquant = super().save(commit=False)
        pratiquant.grade_actuel = self.cleaned_data.get('grade_actuel_nom')
        if commit:
            pratiquant.save()
        return pratiquant
