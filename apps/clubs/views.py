from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Club, DemandeAffiliation, VoletOrganigrammeClub, MembreOrganigrammeClub
from .forms import ClubForm, RejetDemandeForm, VoletOrganigrammeClubForm, MembreOrganigrammeClubForm


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


@gest_ligue_requis
def liste_clubs(request):
    clubs = Club.objects.filter(ligue=request.user.ligue).order_by('nom_club')
    statut_filtre = request.GET.get('statut', '')
    if statut_filtre:
        clubs = clubs.filter(statut_club=statut_filtre)
    return render(request, 'clubs/liste.html', {
        'clubs':         clubs,
        'statut_filtre': statut_filtre,
        'statuts':       Club.STATUT_CHOICES,
    })


@gest_ligue_requis
def creer_club(request):
    if request.method == 'POST':
        form = ClubForm(request.POST, ligue=request.user.ligue)
        if form.is_valid():
            club = form.save(commit=False)
            club.ligue = request.user.ligue
            club.save()
            messages.success(request, f"Club « {club.nom_club} » créé avec succès.")
            return redirect('clubs:liste')
    else:
        form = ClubForm(ligue=request.user.ligue)
    return render(request, 'clubs/form.html', {
        'form':  form,
        'titre': 'Enregistrer un club',
    })


@gest_ligue_requis
def modifier_club(request, pk):
    club = get_object_or_404(Club, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        form = ClubForm(request.POST, instance=club, ligue=request.user.ligue)
        if form.is_valid():
            form.save()
            messages.success(request, f"Club « {club.nom_club} » modifié avec succès.")
            return redirect('clubs:detail', pk=club.pk)
    else:
        form = ClubForm(instance=club, ligue=request.user.ligue)
    return render(request, 'clubs/form.html', {
        'form':  form,
        'titre': f'Modifier — {club.nom_club}',
        'club':  club,
    })


@gest_ligue_requis
def detail_club(request, pk):
    club = get_object_or_404(Club, pk=pk, ligue=request.user.ligue)
    pratiquants = club.pratiquants.select_related('grade_actuel').order_by('nom', 'prenom')
    demandes    = club.demandes_affiliation.select_related('annee_sportive').order_by('-date_demande')
    return render(request, 'clubs/detail.html', {
        'club':        club,
        'pratiquants': pratiquants,
        'demandes':    demandes,
    })


@gest_ligue_requis
def toggle_statut_club(request, pk):
    club = get_object_or_404(Club, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        if club.statut_club == 'AFFILIE':
            club.statut_club = 'SUSPENDU'
            messages.warning(request, f"Club « {club.nom_club} » suspendu.")
        elif club.statut_club == 'SUSPENDU':
            club.statut_club = 'AFFILIE'
            messages.success(request, f"Club « {club.nom_club} » réactivé (affilié).")
        else:
            messages.error(request, "Action non autorisée pour ce statut.")
        club.save()
    return redirect('clubs:liste')


@gest_ligue_requis
def supprimer_club(request, pk):
    club = get_object_or_404(Club, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        if club.pratiquants.exists():
            messages.error(request, f"Impossible de supprimer « {club.nom_club} » : il contient des pratiquants.")
            return redirect('clubs:detail', pk=pk)
        nom = club.nom_club
        club.delete()
        messages.success(request, f"Club « {nom} » supprimé.")
        return redirect('clubs:liste')
    return render(request, 'clubs/confirmer_suppression.html', {'club': club})


@gest_ligue_requis
def demandes_affiliation(request):
    demandes = DemandeAffiliation.objects.filter(
        club__ligue=request.user.ligue,
        statut_affiliation='EN_ATTENTE_VALID_LIGUE'
    ).select_related('club', 'annee_sportive').order_by('-date_demande')
    return render(request, 'clubs/demandes_affiliation.html', {
        'demandes': demandes,
    })


@gest_ligue_requis
def valider_demande(request, pk):
    demande = get_object_or_404(
        DemandeAffiliation, pk=pk,
        club__ligue=request.user.ligue,
        statut_affiliation='EN_ATTENTE_VALID_LIGUE'
    )
    if request.method == 'POST':
        demande.approuver()
        messages.success(request, f"Affiliation de « {demande.club.nom_club} » approuvée.")
        return redirect('clubs:demandes_affiliation')
    return render(request, 'clubs/confirmer_validation.html', {'demande': demande})


@gest_ligue_requis
def rejeter_demande(request, pk):
    demande = get_object_or_404(
        DemandeAffiliation, pk=pk,
        club__ligue=request.user.ligue,
        statut_affiliation='EN_ATTENTE_VALID_LIGUE'
    )
    if request.method == 'POST':
        form = RejetDemandeForm(request.POST)
        if form.is_valid():
            demande.rejeter_par_ligue(motif=form.cleaned_data['motif'])
            messages.warning(request, f"Demande de « {demande.club.nom_club} » rejetée.")
            return redirect('clubs:demandes_affiliation')
    else:
        form = RejetDemandeForm()
    return render(request, 'clubs/rejeter_demande.html', {
        'form':    form,
        'demande': demande,
    })


# ─── Organigramme Club ────────────────────────────────────────────────────────

def gest_club_requis(view_func):
    """Réservé au GEST_CLUB uniquement (pas GEST_LIGUE) pour les actions d'écriture."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_club()):
            messages.error(request, "Accès réservé au Gestionnaire de Club.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


def organigramme_club_acces(view_func):
    """GEST_LIGUE peut voir, GEST_CLUB peut modifier."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_ligue() or request.user.est_gest_club()):
            messages.error(request, "Accès non autorisé.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


@organigramme_club_acces
def organigramme_club(request, club_pk):
    club   = get_object_or_404(Club, pk=club_pk, ligue=request.user.ligue)
    volets = club.volets.prefetch_related('membres').all()
    peut_modifier = request.user.is_superuser or request.user.est_gest_club()
    return render(request, 'clubs/organigramme.html', {
        'club':          club,
        'volets':        volets,
        'peut_modifier': peut_modifier,
    })


@gest_club_requis
def creer_volet_club(request, club_pk):
    club = get_object_or_404(Club, pk=club_pk, ligue=request.user.ligue)
    if request.method == 'POST':
        form = VoletOrganigrammeClubForm(request.POST)
        if form.is_valid():
            volet = form.save(commit=False)
            volet.club  = club
            volet.ordre = club.volets.count()
            volet.save()
            messages.success(request, f"Volet « {volet.nom_volet} » créé.")
    return redirect('clubs:organigramme', club_pk=club.pk)


@gest_club_requis
def modifier_volet_club(request, pk):
    volet = get_object_or_404(VoletOrganigrammeClub, pk=pk, club__ligue=request.user.ligue)
    if request.method == 'POST':
        form = VoletOrganigrammeClubForm(request.POST, instance=volet)
        if form.is_valid():
            form.save()
            messages.success(request, "Volet modifié.")
    return redirect('clubs:organigramme', club_pk=volet.club.pk)


@gest_club_requis
def supprimer_volet_club(request, pk):
    volet = get_object_or_404(VoletOrganigrammeClub, pk=pk, club__ligue=request.user.ligue)
    club_pk = volet.club.pk
    if request.method == 'POST':
        if volet.membres.exists():
            messages.error(request, "Impossible de supprimer un volet qui contient des membres.")
        else:
            volet.delete()
            messages.success(request, "Volet supprimé.")
    return redirect('clubs:organigramme', club_pk=club_pk)


@gest_club_requis
def ajouter_membre_club(request, volet_pk):
    volet = get_object_or_404(VoletOrganigrammeClub, pk=volet_pk, club__ligue=request.user.ligue)
    if request.method == 'POST':
        form = MembreOrganigrammeClubForm(request.POST)
        if form.is_valid():
            membre = form.save(commit=False)
            membre.volet = volet
            membre.save()
            messages.success(request, f"{membre.prenom} {membre.nom} ajouté.")
    return redirect('clubs:organigramme', club_pk=volet.club.pk)


@gest_club_requis
def modifier_membre_club(request, pk):
    membre = get_object_or_404(MembreOrganigrammeClub, pk=pk, volet__club__ligue=request.user.ligue)
    if request.method == 'POST':
        form = MembreOrganigrammeClubForm(request.POST, instance=membre)
        if form.is_valid():
            form.save()
            messages.success(request, "Membre modifié.")
    return redirect('clubs:organigramme', club_pk=membre.volet.club.pk)


@gest_club_requis
def toggle_actif_membre_club(request, pk):
    membre = get_object_or_404(MembreOrganigrammeClub, pk=pk, volet__club__ligue=request.user.ligue)
    club_pk = membre.volet.club.pk
    membre.actif = not membre.actif
    membre.save()
    etat = "activé" if membre.actif else "désactivé"
    messages.success(request, f"{membre.prenom} {membre.nom} {etat}.")
    return redirect('clubs:organigramme', club_pk=club_pk)


@gest_club_requis
def supprimer_membre_club(request, pk):
    membre = get_object_or_404(MembreOrganigrammeClub, pk=pk, volet__club__ligue=request.user.ligue)
    club_pk = membre.volet.club.pk
    if request.method == 'POST':
        nom = f"{membre.prenom} {membre.nom}"
        membre.delete()
        messages.success(request, f"{nom} supprimé de l'organigramme.")
    return redirect('clubs:organigramme', club_pk=club_pk)
