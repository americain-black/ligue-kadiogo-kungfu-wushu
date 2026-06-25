from django import forms
from .models import Pratiquant, Grade


class PratiquantForm(forms.ModelForm):
    class Meta:
        model  = Pratiquant
        fields = ['nom', 'prenom', 'date_naissance', 'sexe', 'lieu_naissance',
                  'telephone', 'grade_actuel', 'photo', 'actif']
        widgets = {
            'nom':             forms.TextInput(attrs={'class': 'form-control'}),
            'prenom':          forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance':  forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe':            forms.Select(attrs={'class': 'form-select'}),
            'lieu_naissance':  forms.TextInput(attrs={'class': 'form-control'}),
            'telephone':       forms.TextInput(attrs={'class': 'form-control'}),
            'grade_actuel':    forms.Select(attrs={'class': 'form-select'}),
            'photo':           forms.FileInput(attrs={'class': 'form-control'}),
            'actif':           forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nom':            'Nom',
            'prenom':         'Prénom',
            'date_naissance': 'Date de naissance',
            'sexe':           'Sexe',
            'lieu_naissance': 'Lieu de naissance',
            'telephone':      'Téléphone',
            'grade_actuel':   'Grade actuel',
            'photo':          'Photo',
            'actif':          'Pratiquant actif',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grade_actuel'].empty_label = '--- Pas de grade ---'
        self.fields['grade_actuel'].queryset = Grade.objects.filter(actif=True).order_by('ordre')
        self.fields['grade_actuel'].required = False
