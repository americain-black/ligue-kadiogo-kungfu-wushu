# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect, get_object_or_404
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [missing-import]
from django.contrib import messages
from .models import Ligue, VoletOrganigramme, MembreOrganigramme
from .forms import LigueForm, VoletOrganigrammeForm, MembreOrganigrammeForm, EditerInfosLigueForm


def super_admin_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_super_admin()):
            messages.error(request, "Accès réservé au Super Administrateur.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


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


@super_admin_requis
def liste_ligues(request):
    ligues = Ligue.objects.all().order_by('nom_ligue')
    return render(request, 'ligues/liste.html', {'ligues': ligues})


@super_admin_requis
def creer_ligue(request):
    if request.method == 'POST':
        form = LigueForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Ligue créée avec succès.")
            return redirect('ligues:liste')
    else:
        form = LigueForm()
    return render(request, 'ligues/form.html', {'form': form, 'titre': 'Créer une ligue'})


@super_admin_requis
def modifier_ligue(request, pk):
    ligue = get_object_or_404(Ligue, pk=pk)
    if request.method == 'POST':
        form = LigueForm(request.POST, request.FILES, instance=ligue)
        if form.is_valid():
            form.save()
            messages.success(request, "Ligue modifiée avec succès.")
            return redirect('ligues:liste')
    else:
        form = LigueForm(instance=ligue)
    return render(request, 'ligues/form.html', {
        'form': form, 'titre': 'Modifier la ligue', 'ligue': ligue
    })


@super_admin_requis
def toggle_statut_ligue(request, pk):
    ligue = get_object_or_404(Ligue, pk=pk)
    if ligue.statut == 'ACTIVE':
        ligue.statut = 'INACTIVE'
        messages.warning(request, f"Ligue « {ligue.nom_ligue} » désactivée.")
    else:
        ligue.statut = 'ACTIVE'
        messages.success(request, f"Ligue « {ligue.nom_ligue} » réactivée.")
    ligue.save()
    return redirect('ligues:liste')


@super_admin_requis
def supprimer_ligue(request, pk):
    # pyrefly: ignore [missing-import]
    from django.db import transaction
    ligue  = get_object_or_404(Ligue, pk=pk)
    clubs  = list(ligue.clubs.all().order_by('nom_club'))
    nb_utilisateurs = ligue.utilisateurs.count()

    if request.method == 'POST':
        from apps.practitioners.models import Pratiquant
        from apps.exams.models import (
            Inscription, SessionExamen, AnneeSportive,
            TarifExamen, AffectationJury
        )
        from apps.payments.models import PaiementExamen

        with transaction.atomic():
            # Cascade manuelle (FKs PROTECT empêchent la suppression automatique)
            Inscription.objects.filter(session__annee_sportive__ligue=ligue).delete()
            PaiementExamen.objects.filter(session__annee_sportive__ligue=ligue).delete()
            AffectationJury.objects.filter(session__annee_sportive__ligue=ligue).delete()
            TarifExamen.objects.filter(annee_sportive__ligue=ligue).delete()
            SessionExamen.objects.filter(annee_sportive__ligue=ligue).delete()
            AnneeSportive.objects.filter(ligue=ligue).delete()
            Pratiquant.objects.filter(club__ligue=ligue).delete()
            # Détacher les gestionnaires de club pour éviter ProtectedError
            ligue.clubs.update(utilisateur=None)
            ligue.clubs.all().delete()
            nom = ligue.nom_ligue
            ligue.delete()

        messages.success(request, f"Ligue « {nom} » et toutes ses données supprimées.")
        return redirect('ligues:liste')

    return render(request, 'ligues/confirmer_suppression.html', {
        'ligue':          ligue,
        'clubs':          clubs,
        'nb_utilisateurs': nb_utilisateurs,
    })


# ─── Organigramme ────────────────────────────────────────────────────────────

@gest_ligue_requis
def organigramme(request):
    ligue = request.user.ligue
    volets = ligue.volets.prefetch_related('membres__club').all()
    for v in volets:
        v.membres_du_volet = v.membres.filter(club__isnull=True)
    form_volet = VoletOrganigrammeForm()
    clubs = ligue.clubs.all().order_by('nom_club')
    return render(request, 'ligues/organigramme.html', {
        'ligue':            ligue,
        'volets':           volets,
        'form_volet':       form_volet,
        'fonction_choices': MembreOrganigramme.FONCTION_CHOICES,
        'clubs':            clubs,
    })


def organigramme_visuel(request):
    if request.user.is_authenticated and getattr(request.user, 'ligue', None):
        ligue = request.user.ligue
    else:
        ligue = Ligue.objects.filter(sigle='LKKFW').first() or Ligue.objects.first()

    if not ligue:
        messages.error(request, "Aucune ligue trouvée.")
        return redirect('accounts:accueil')

    ordre_fonctions = [code for code, _ in MembreOrganigramme.FONCTION_CHOICES]
    volets = ligue.volets.prefetch_related('membres__club').all()
    for volet in volets:
        volet.membres_actifs = sorted(
            volet.membres.filter(actif=True, club__isnull=True),
            key=lambda m: ordre_fonctions.index(m.fonction) if m.fonction in ordre_fonctions else 999
        )
    return render(request, 'ligues/organigramme_visuel.html', {
        'ligue':            ligue,
        'volets':           volets,
        'fonction_choices': MembreOrganigramme.FONCTION_CHOICES,
    })


@gest_ligue_requis
def creer_volet(request):
    if request.method == 'POST':
        form = VoletOrganigrammeForm(request.POST)
        if form.is_valid():
            volet = form.save(commit=False)
            volet.ligue = request.user.ligue
            volet.ordre = request.user.ligue.volets.count()
            volet.save()
            messages.success(request, f"Volet « {volet.nom_volet} » créé.")
    return redirect('ligues:organigramme')


@gest_ligue_requis
def modifier_volet(request, pk):
    volet = get_object_or_404(VoletOrganigramme, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        form = VoletOrganigrammeForm(request.POST, instance=volet)
        if form.is_valid():
            form.save()
            messages.success(request, "Volet modifié.")
    return redirect('ligues:organigramme')


@gest_ligue_requis
def supprimer_volet(request, pk):
    volet = get_object_or_404(VoletOrganigramme, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        if volet.membres.exists():
            messages.error(request, "Impossible de supprimer un volet qui contient des membres.")
        else:
            volet.delete()
            messages.success(request, "Volet supprimé.")
    return redirect('ligues:organigramme')


@gest_ligue_requis
def ajouter_membre(request, volet_pk):
    volet = get_object_or_404(VoletOrganigramme, pk=volet_pk, ligue=request.user.ligue)
    if request.method == 'POST':
        form = MembreOrganigrammeForm(request.POST)
        if form.is_valid():
            membre = form.save(commit=False)
            membre.volet = volet
            club_id = request.POST.get('club')
            if club_id:
                from apps.clubs.models import Club
                membre.club = Club.objects.filter(pk=club_id, ligue=request.user.ligue).first()
            membre.save()
            messages.success(request, f"{membre.prenom} {membre.nom} ajouté.")
    return redirect('ligues:organigramme')


@gest_ligue_requis
def modifier_membre(request, pk):
    membre = get_object_or_404(MembreOrganigramme, pk=pk, volet__ligue=request.user.ligue)
    if request.method == 'POST':
        form = MembreOrganigrammeForm(request.POST, instance=membre)
        if form.is_valid():
            m = form.save(commit=False)
            club_id = request.POST.get('club')
            if club_id:
                from apps.clubs.models import Club
                m.club = Club.objects.filter(pk=club_id, ligue=request.user.ligue).first()
            else:
                m.club = None
            m.save()
            messages.success(request, "Membre modifié.")
    return redirect('ligues:organigramme')


@gest_ligue_requis
def toggle_actif_membre(request, pk):
    membre = get_object_or_404(MembreOrganigramme, pk=pk, volet__ligue=request.user.ligue)
    membre.actif = not membre.actif
    membre.save()
    etat = "activé" if membre.actif else "désactivé"
    messages.success(request, f"{membre.prenom} {membre.nom} {etat}.")
    return redirect('ligues:organigramme')


@gest_ligue_requis
def supprimer_membre(request, pk):
    membre = get_object_or_404(MembreOrganigramme, pk=pk, volet__ligue=request.user.ligue)
    if request.method == 'POST':
        nom = f"{membre.prenom} {membre.nom}"
        membre.delete()
        messages.success(request, f"{nom} supprimé de l'organigramme.")
    return redirect('ligues:organigramme')


@gest_ligue_requis
def editer_infos_ligue(request):
    """Permet au gestionnaire de ligue de modifier le contenu À Propos, Présentation, Misions et Contact."""
    ligue = request.user.ligue
    if not ligue and request.user.is_superuser:
        ligue = Ligue.objects.filter(sigle='LKKFW').first() or Ligue.objects.first()

    if not ligue:
        messages.error(request, "Aucune ligue associée à votre compte.")
        return redirect('accounts:tableau_de_bord')

    if request.method == 'POST':
        form = EditerInfosLigueForm(request.POST, request.FILES, instance=ligue)
        if form.is_valid():
            form.save()
            messages.success(request, "Les informations et présentations de la ligue ont été mises à jour avec succès.")
            return redirect('ligues:editer_infos')
    else:
        form = EditerInfosLigueForm(instance=ligue)

    return render(request, 'ligues/editer_infos.html', {
        'ligue': ligue,
        'form': form,
    })
