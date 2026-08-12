from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Utilisateur, Role


class UtilisateurCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model  = Utilisateur
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'telephone', 'ligue', 'photo',
        ]
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone':  forms.TextInput(attrs={'class': 'form-control'}),
            'ligue':      forms.Select(attrs={'class': 'form-select'}),
            'photo':      forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        if p1:
            validate_password(p1)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UtilisateurLigueCreationForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.exclude(nom_role=Role.SUPER_ADMIN),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Rôle / Fonction dans la Ligue ou Club",
        empty_label="-- Sélectionner le rôle --",
        required=True
    )
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe sécurisé'}),
    )
    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmer le mot de passe'}),
    )

    class Meta:
        model  = Utilisateur
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'telephone', 'sexe', 'photo',
        ]
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: d_technique_kadiogo'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@domaine.bf'}),
            'telephone':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+226 70 00 00 00'}),
            'sexe':       forms.Select(attrs={'class': 'form-select'}),
            'photo':      forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        if p1:
            validate_password(p1)
        return cleaned_data

    def save(self, ligue=None, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if ligue:
            user.ligue = ligue
        if commit:
            user.save()
            role = self.cleaned_data.get('role')
            if role:
                from .models import UtilisateurRole
                UtilisateurRole.objects.get_or_create(utilisateur=user, role=role)
        return user


class UtilisateurModificationForm(forms.ModelForm):
    class Meta:
        model  = Utilisateur
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'telephone', 'ligue', 'photo',
        ]
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone':  forms.TextInput(attrs={'class': 'form-control'}),
            'ligue':      forms.Select(attrs={'class': 'form-select'}),
            'photo':      forms.FileInput(attrs={'class': 'form-control'}),
        }


class RolesForm(forms.Form):
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Rôles'
    )

    def clean_roles(self):
        roles = self.cleaned_data.get('roles', [])
        noms  = {r.nom_role for r in roles}
        if not noms:
            return roles

        # SUPER_ADMIN est toujours exclusif
        if Role.SUPER_ADMIN in noms and len(noms) > 1:
            raise forms.ValidationError(
                "Le Super Administrateur ne peut pas avoir d'autres rôles."
            )

        # Multi-rôles uniquement si GEST_LIGUE est le rôle principal
        if len(noms) > 1 and Role.GEST_LIGUE not in noms:
            raise forms.ValidationError(
                "Seul un Gestionnaire de Ligue peut avoir des rôles supplémentaires."
            )

        # Les rôles supplémentaires autorisés pour GEST_LIGUE
        if Role.GEST_LIGUE in noms:
            autorises = {Role.GEST_LIGUE, Role.GEST_CLUB, Role.GEST_FINANCIER, Role.JURY}
            interdits = noms - autorises
            if interdits:
                raise forms.ValidationError(
                    "Un Gestionnaire de Ligue peut cumuler uniquement : "
                    "Gestionnaire Club, Gestionnaire Financier, Jury."
                )

        return roles


class MonProfilForm(forms.ModelForm):
    nouveau_mot_de_passe = forms.CharField(
        label="Nouveau mot de passe (laisser vide pour ne pas modifier)",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nouveau mot de passe'}),
        required=False
    )
    confirmer_mot_de_passe = forms.CharField(
        label="Confirmer le nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmer mot de passe'}),
        required=False
    )

    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'username', 'email', 'telephone', 'sexe', 'photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone':  forms.TextInput(attrs={'class': 'form-control'}),
            'sexe':       forms.Select(attrs={'class': 'form-select'}),
            'photo':      forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('nouveau_mot_de_passe')
        p2 = cleaned_data.get('confirmer_mot_de_passe')
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
            if p1:
                validate_password(p1, self.instance)
        return cleaned_data
