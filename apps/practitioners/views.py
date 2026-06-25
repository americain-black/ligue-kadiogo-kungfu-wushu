from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from .models import Pratiquant
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
    club = request.user.club
    if request.method == 'POST':
        form = PratiquantForm(request.POST, request.FILES)
        if form.is_valid():
            pratiquant = form.save(commit=False)
            pratiquant.club = club
            pratiquant.save()
            messages.success(request, f"{pratiquant.prenom} {pratiquant.nom} inscrit avec succès.")
            return redirect('practitioners:liste')
    else:
        form = PratiquantForm()
    return render(request, 'practitioners/form.html', {
        'form':  form,
        'titre': 'Inscrire un pratiquant',
        'club':  club,
    })


@gest_club_requis
def modifier_pratiquant(request, pk):
    club       = request.user.club
    pratiquant = get_object_or_404(Pratiquant, pk=pk, club=club)
    if request.method == 'POST':
        form = PratiquantForm(request.POST, request.FILES, instance=pratiquant)
        if form.is_valid():
            form.save()
            messages.success(request, f"{pratiquant.prenom} {pratiquant.nom} modifié.")
            return redirect('practitioners:liste')
    else:
        form = PratiquantForm(instance=pratiquant)
    return render(request, 'practitioners/form.html', {
        'form':       form,
        'titre':      f'Modifier — {pratiquant.prenom} {pratiquant.nom}',
        'pratiquant': pratiquant,
        'club':       club,
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
