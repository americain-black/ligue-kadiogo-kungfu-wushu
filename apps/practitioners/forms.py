from django import forms
from .models import Pratiquant, Grade


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
        if ligue:
            qs = Grade.objects.filter(ligue=ligue, actif=True).order_by('id_grade')
        else:
            qs = Grade.objects.filter(actif=True).order_by('id_grade')
        self.fields['grade_actuel_nom'].queryset = qs
        if self.instance and self.instance.pk and self.instance.grade_actuel:
            self.initial['grade_actuel_nom'] = self.instance.grade_actuel

    def save(self, commit=True):
        pratiquant = super().save(commit=False)
        pratiquant.grade_actuel = self.cleaned_data.get('grade_actuel_nom')
        if commit:
            pratiquant.save()
        return pratiquant
