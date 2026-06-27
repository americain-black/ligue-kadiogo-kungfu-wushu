from django import forms as django_forms
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from .models import Pratiquant, Grade
from .forms import PratiquantForm


def gest_club_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_club()):
            messages.error(request, "Accès réservé au Gestionnaire de Club.")
            return redirect('accounts:tableau_de_bord')
        if not hasattr(request.user, 'club') and not request.user.is_superuser:
            messages.error(request, "Votre compte n'est rattaché à aucun club.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


@gest_club_requis
def liste_pratiquants(request):
    club = request.user.club
    pratiquants = Pratiquant.objects.filter(club=club).select_related('grade_actuel')

    filtre = request.GET.get('statut', 'actif')
    if filtre == 'inactif':
        pratiquants = pratiquants.filter(actif=False)
    else:
        pratiquants = pratiquants.filter(actif=True)

    return render(request, 'practitioners/liste.html', {
        'pratiquants': pratiquants,
        'club':        club,
        'filtre':      filtre,
    })


@gest_club_requis
def ajouter_pratiquant(request):
    club  = request.user.club
    ligue = club.ligue
    if request.method == 'POST':
        form = PratiquantForm(request.POST, request.FILES, ligue=ligue)
        if form.is_valid():
            pratiquant = form.save(commit=False)
            pratiquant.club = club
            pratiquant.save()
            messages.success(request, f"{pratiquant.prenom} {pratiquant.nom} inscrit avec succès.")
            return redirect('practitioners:liste')
    else:
        form = PratiquantForm(ligue=ligue)
    return render(request, 'practitioners/form.html', {
        'form':   form,
        'titre':  'Inscrire un pratiquant',
        'club':   club,
        'grades': Grade.objects.filter(ligue=ligue, actif=True).order_by('ordre'),
    })


@gest_club_requis
def modifier_pratiquant(request, pk):
    club       = request.user.club
    ligue      = club.ligue
    pratiquant = get_object_or_404(Pratiquant, pk=pk, club=club)
    if request.method == 'POST':
        form = PratiquantForm(request.POST, request.FILES, instance=pratiquant, ligue=ligue)
        if form.is_valid():
            form.save()
            messages.success(request, f"{pratiquant.prenom} {pratiquant.nom} modifié.")
            return redirect('practitioners:liste')
    else:
        form = PratiquantForm(instance=pratiquant, ligue=ligue)
    return render(request, 'practitioners/form.html', {
        'form':       form,
        'titre':      f'Modifier — {pratiquant.prenom} {pratiquant.nom}',
        'pratiquant': pratiquant,
        'club':       club,
        'grades':     Grade.objects.filter(ligue=ligue, actif=True).order_by('ordre'),
    })


@gest_club_requis
def detail_pratiquant(request, pk):
    club       = request.user.club
    pratiquant = get_object_or_404(Pratiquant, pk=pk, club=club)
    return render(request, 'practitioners/detail.html', {
        'pratiquant': pratiquant,
        'club':       club,
    })


@gest_club_requis
def toggle_actif_pratiquant(request, pk):
    club       = request.user.club
    pratiquant = get_object_or_404(Pratiquant, pk=pk, club=club)
    if request.method == 'POST':
        pratiquant.actif = not pratiquant.actif
        pratiquant.save()
        etat = "activé" if pratiquant.actif else "désactivé"
        messages.success(request, f"{pratiquant.prenom} {pratiquant.nom} {etat}.")
    return redirect('practitioners:liste')


@gest_club_requis
def supprimer_pratiquant(request, pk):
    club       = request.user.club
    pratiquant = get_object_or_404(Pratiquant, pk=pk, club=club)
    if request.method == 'POST':
        nom_complet = f"{pratiquant.prenom} {pratiquant.nom}"
        try:
            pratiquant.delete()
            messages.success(request, f"{nom_complet} supprimé.")
        except ProtectedError:
            messages.error(
                request,
                f"Impossible de supprimer {nom_complet} : il est inscrit à une ou plusieurs sessions d'examen."
            )
    return redirect('practitioners:liste')


# ── Vues GEST_LIGUE — Gestion des grades ──────────────────────────────────────

def gest_ligue_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_ligue()):
            messages.error(request, "Accès réservé au Gestionnaire de Ligue.")
            return redirect('accounts:tableau_de_bord')
        if not request.user.ligue and not request.user.is_superuser:
            messages.error(request, "Votre compte n'est rattaché à aucune ligue.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


class GradeForm(django_forms.ModelForm):
    # Déclaré comme CharField pour éviter la validation entier automatique de Django
    ordre = django_forms.CharField(
        label='Ordre (chiffre romain)',
        widget=django_forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'Ex : I, II, III, IV…',
        }),
    )

    class Meta:
        model  = Grade
        fields = ['id_grade', 'nom', 'ordre', 'actif']
        widgets = {
            'id_grade': django_forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'nom':      django_forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Blanc, Jaune, Vert…'}),
            'actif':    django_forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'id_grade': 'ID Grade (auto)',
            'nom':      'Nom du grade',
            'actif':    'Grade actif',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Afficher la valeur actuelle en chiffre romain lors de la modification
        if self.instance and self.instance.pk and self.instance.ordre:
            from .models import _to_romain
            self.initial['ordre'] = _to_romain(self.instance.ordre)

    def clean_ordre(self):
        from .models import _from_romain
        val = str(self.cleaned_data.get('ordre', '')).strip().upper()
        if not val:
            raise django_forms.ValidationError("L'ordre est requis.")
        # Accepter aussi les chiffres arabes directs (1, 2, 3…)
        n = int(val) if val.isdigit() else _from_romain(val)
        if n <= 0:
            raise django_forms.ValidationError(
                f"« {val} » n'est pas un chiffre romain valide (ex : I, II, III, IV…)."
            )
        return n


@gest_ligue_requis
def liste_grades(request):
    ligue  = request.user.ligue
    grades = Grade.objects.filter(ligue=ligue).order_by('ordre')
    return render(request, 'practitioners/grades_liste.html', {
        'grades': grades,
        'ligue':  ligue,
    })


@gest_ligue_requis
def creer_grade(request):
    from django.db.models import Max
    ligue  = request.user.ligue
    max_id = Grade.objects.filter(ligue=ligue).aggregate(m=Max('id_grade'))['m'] or 0
    prochain_id = max_id + 1
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.ligue    = ligue
            grade.id_grade = prochain_id  # toujours forcé côté serveur
            grade.save()
            messages.success(request, f"Grade « {grade.nom} » créé (ID {grade.id_grade}).")
            return redirect('practitioners:grades')
    else:
        form = GradeForm(initial={'id_grade': prochain_id})
    return render(request, 'practitioners/grade_form.html', {
        'form':        form,
        'titre':       'Créer un grade',
        'prochain_id': prochain_id,
    })


@gest_ligue_requis
def modifier_grade(request, pk):
    ligue = request.user.ligue
    grade = get_object_or_404(Grade, pk=pk, ligue=ligue)
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade)
        if form.is_valid():
            g = form.save(commit=False)
            g.id_grade = grade.id_grade  # id_grade immuable
            g.save()
            messages.success(request, f"Grade « {grade.nom} » modifié.")
            return redirect('practitioners:grades')
    else:
        form = GradeForm(instance=grade)
    return render(request, 'practitioners/grade_form.html', {
        'form':  form,
        'titre': f'Modifier — {grade.nom}',
        'grade': grade,
    })


@gest_ligue_requis
def supprimer_grade(request, pk):
    ligue = request.user.ligue
    grade = get_object_or_404(Grade, pk=pk, ligue=ligue)
    if request.method == 'POST':
        try:
            nom = grade.nom
            grade.delete()
            messages.success(request, f"Grade « {nom} » supprimé.")
        except ProtectedError:
            messages.error(
                request,
                f"Impossible de supprimer « {grade.nom} » : des pratiquants ou inscriptions y sont liés."
            )
    return redirect('practitioners:grades')


@gest_ligue_requis
def toggle_actif_grade(request, pk):
    ligue = request.user.ligue
    grade = get_object_or_404(Grade, pk=pk, ligue=ligue)
    if request.method == 'POST':
        grade.actif = not grade.actif
        grade.save()
        etat = "activé" if grade.actif else "désactivé"
        messages.success(request, f"Grade « {grade.nom} » {etat}.")
    return redirect('practitioners:grades')
