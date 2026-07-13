from django import forms as django_forms
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
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
    club  = request.user.club
    ligue = club.ligue

    filtre_statut     = request.GET.get('statut', 'actif')
    filtre_grade      = request.GET.get('grade', '')
    filtre_sexe       = request.GET.get('sexe', '')
    filtre_recherche  = request.GET.get('q', '').strip()

    pratiquants = Pratiquant.objects.filter(club=club).select_related('grade_actuel')

    if filtre_statut == 'inactif':
        pratiquants = pratiquants.filter(actif=False)
    else:
        pratiquants = pratiquants.filter(actif=True)

    if filtre_grade == 'sans':
        pratiquants = pratiquants.filter(grade_actuel__isnull=True)
    elif filtre_grade:
        pratiquants = pratiquants.filter(grade_actuel__pk=filtre_grade)

    if filtre_sexe:
        pratiquants = pratiquants.filter(sexe=filtre_sexe)

    if filtre_recherche:
        pratiquants = pratiquants.filter(
            Q(nom__icontains=filtre_recherche) | Q(prenom__icontains=filtre_recherche)
        )

    grades = Grade.objects.filter(ligue=ligue).order_by('id_grade')

    filtre_grade_nom = ''
    if filtre_grade == 'sans':
        filtre_grade_nom = 'Sans grade'
    elif filtre_grade:
        grade_obj = grades.filter(pk=filtre_grade).first()
        filtre_grade_nom = grade_obj.nom if grade_obj else ''

    return render(request, 'practitioners/liste.html', {
        'pratiquants':       pratiquants,
        'club':              club,
        'filtre':            filtre_statut,
        'filtre_grade':      filtre_grade,
        'filtre_grade_nom':  filtre_grade_nom,
        'filtre_sexe':       filtre_sexe,
        'filtre_recherche':  filtre_recherche,
        'grades':            grades,
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
    import json
    grades_qs = Grade.objects.filter(ligue=ligue, actif=True).order_by('id_grade')
    grades_json = json.dumps({str(g.pk): g.id_grade for g in grades_qs})
    return render(request, 'practitioners/form.html', {
        'form':        form,
        'titre':       'Inscrire un pratiquant',
        'club':        club,
        'grades':      grades_qs,
        'grades_json': grades_json,
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
    import json
    grades_qs = Grade.objects.filter(ligue=ligue, actif=True).order_by('id_grade')
    grades_json = json.dumps({str(g.pk): g.id_grade for g in grades_qs})
    return render(request, 'practitioners/form.html', {
        'form':        form,
        'titre':       f'Modifier — {pratiquant.prenom} {pratiquant.nom}',
        'pratiquant':  pratiquant,
        'club':        club,
        'grades':      grades_qs,
        'grades_json': grades_json,
    })


@gest_club_requis
def detail_pratiquant(request, pk):
    club       = request.user.club
    pratiquant = get_object_or_404(Pratiquant, pk=pk, club=club)
    resultats  = (
        pratiquant.inscriptions
        .filter(resultat__publie=True)
        .select_related('session', 'grade_vise', 'resultat')
        .order_by('-session__date_examen')
    )
    return render(request, 'practitioners/detail.html', {
        'pratiquant': pratiquant,
        'club':       club,
        'resultats':  resultats,
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
    inscriptions = pratiquant.inscriptions.select_related('session', 'grade_vise').order_by('-session__date_examen')
    has_valide   = inscriptions.filter(statut__in=['PAIEMENT_VALIDE', 'AUTORISE']).exists()

    if request.method == 'POST':
        nom_complet = f"{pratiquant.prenom} {pratiquant.nom}"
        pratiquant.delete()   # CASCADE supprime aussi les inscriptions
        messages.success(request, f"{nom_complet} supprimé définitivement du club.")
        return redirect('practitioners:liste')

    return render(request, 'practitioners/confirmer_supprimer.html', {
        'pratiquant':   pratiquant,
        'inscriptions': inscriptions,
        'has_valide':   has_valide,
        'club':         club,
    })


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
    class Meta:
        model  = Grade
        fields = ['nom', 'actif']
        widgets = {
            'nom':   django_forms.TextInput(attrs={
                'class': 'form-control text-uppercase',
                'placeholder': 'Ex : BLANC, ROUGE, ROUGE I, ROUGE II…',
            }),
            'actif': django_forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nom':   'Nom du grade',
            'actif': 'Grade actif',
        }


@gest_ligue_requis
def liste_grades(request):
    ligue  = request.user.ligue
    grades = Grade.objects.filter(ligue=ligue).order_by('id_grade')
    return render(request, 'practitioners/grades_liste.html', {
        'grades':      grades,
        'ligue':       ligue,
        'nb_actifs':   grades.filter(actif=True).count(),
        'nb_inactifs': grades.filter(actif=False).count(),
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

    # Inscriptions → PROTECT (bloquant)
    inscriptions    = grade.inscriptions.select_related('session', 'pratiquant').order_by('-session__date_examen')
    nb_inscriptions = inscriptions.count()
    # Pratiquants → SET_NULL (grade devient "Sans grade")
    pratiquants     = grade.pratiquants.select_related('club').order_by('nom', 'prenom')
    nb_pratiquants  = pratiquants.count()
    # Tarifs et rubriques → CASCADE (supprimés avec le grade)
    tarifs          = grade.tarifs.select_related('annee_sportive')
    nb_tarifs       = tarifs.count()
    rubriques       = grade.rubrique_grades.select_related('rubrique')
    nb_rubriques    = rubriques.count()

    peut_supprimer  = nb_inscriptions == 0

    if request.method == 'POST':
        if not peut_supprimer:
            messages.error(request, f"Impossible : {nb_inscriptions} inscription(s) utilisent ce grade.")
            return redirect('practitioners:supprimer_grade', pk=pk)
        nom = grade.nom
        grade.delete()  # CASCADE → tarifs + rubriques supprimés ; SET_NULL → grade_actuel des pratiquants
        messages.success(
            request,
            f"Grade « {nom} » supprimé"
            + (f" — {nb_pratiquants} pratiquant(s) sans grade" if nb_pratiquants else "")
            + (f" — {nb_tarifs} tarif(s) supprimé(s)" if nb_tarifs else "")
            + "."
        )
        return redirect('practitioners:grades')

    return render(request, 'practitioners/confirmer_supprimer_grade.html', {
        'grade':           grade,
        'inscriptions':    inscriptions[:10],
        'nb_inscriptions': nb_inscriptions,
        'pratiquants':     pratiquants,
        'nb_pratiquants':  nb_pratiquants,
        'tarifs':          tarifs,
        'nb_tarifs':       nb_tarifs,
        'rubriques':       rubriques,
        'nb_rubriques':    nb_rubriques,
        'peut_supprimer':  peut_supprimer,
    })


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
