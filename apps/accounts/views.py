from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Utilisateur, Role, UtilisateurRole
from .forms import UtilisateurCreationForm, UtilisateurModificationForm, RolesForm


def super_admin_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_super_admin()):
            messages.error(request, "Accès réservé au Super Administrateur.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


def connexion(request):
    if request.user.is_authenticated:
        return redirect('accounts:tableau_de_bord')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user     = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.statut_compte:
                messages.error(request, "Votre compte est désactivé. Contactez l'administrateur.")
                return render(request, 'accounts/login.html')

            login(request, user)
            return redirect('accounts:tableau_de_bord')
        else:
            return render(request, 'accounts/login.html', {'form': {'errors': True}})

    return render(request, 'accounts/login.html')


def deconnexion(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def tableau_de_bord(request):
    user = request.user

    # is_superuser (createsuperuser) est traité comme Super Admin
    if user.is_superuser or user.est_super_admin():
        return redirect('accounts:dashboard_super_admin')
    elif user.est_gest_ligue():
        return redirect('accounts:dashboard_ligue')
    elif user.est_gest_club():
        return redirect('accounts:dashboard_club')
    elif user.est_gest_financier():
        return redirect('accounts:dashboard_financier')
    elif user.est_jury():
        return redirect('accounts:dashboard_jury')
    else:
        messages.warning(request, "Aucun rôle attribué à votre compte. Contactez l'administrateur.")
        logout(request)
        return redirect('accounts:login')


@login_required
def dashboard_super_admin(request):
    from apps.ligues.models import Ligue
    contexte = {
        'nb_ligues_actives':   Ligue.objects.filter(statut='ACTIVE').count(),
        'nb_ligues_total':     Ligue.objects.count(),
        'nb_utilisateurs':     Utilisateur.objects.filter(is_superuser=False).count(),
        'nb_actifs':           Utilisateur.objects.filter(statut_compte=True, is_superuser=False).count(),
        'dernieres_ligues':    Ligue.objects.order_by('-date_creation')[:5],
        'derniers_utilisateurs': Utilisateur.objects.filter(is_superuser=False).order_by('-date_joined')[:5],
    }
    return render(request, 'accounts/dashboard_super_admin.html', contexte)


@login_required
def dashboard_ligue(request):
    from apps.clubs.models import Club, DemandeAffiliation
    from apps.practitioners.models import Pratiquant, Grade
    from apps.exams.models import SessionExamen, Inscription, AnneeSportive, TarifExamen
    from django.db.models import Count, Q

    ligue = request.user.ligue

    if not ligue:
        messages.warning(request, "Votre compte n'est rattaché à aucune ligue.")
        return render(request, 'accounts/dashboard_ligue.html', {'ligue': None})

    clubs_qs   = Club.objects.filter(ligue=ligue)
    demandes_qs = DemandeAffiliation.objects.filter(
        club__ligue=ligue,
        statut_affiliation='EN_ATTENTE_VALID_LIGUE'
    )

    # Dernière session active
    derniere_session = (
        SessionExamen.objects
        .filter(annee_sportive__ligue=ligue)
        .exclude(statut='RESULTATS_PUBLIES')
        .order_by('-date_examen')
        .first()
    )

    # Licenciés = pratiquants inscrits à la dernière session
    nb_licencies = 0
    clubs_resume = []
    if derniere_session:
        nb_licencies = Inscription.objects.filter(session=derniere_session).count()

        # Résumé par club pour la session
        from apps.clubs.models import Club
        for club in Club.objects.filter(ligue=ligue).order_by('nom_club'):
            qs_club = Inscription.objects.filter(session=derniere_session, pratiquant__club=club)
            total      = qs_club.count()
            if total == 0:
                continue
            nb_autorises = qs_club.filter(statut='AUTORISE').count()
            nb_attente   = qs_club.filter(statut='EN_ATTENTE_PAIEMENT').count()
            clubs_resume.append({
                'nom':          club.nom_club,
                'nb_inscrits':  total,
                'nb_autorises': nb_autorises,
                'nb_attente':   nb_attente,
            })

    # Année sportive active + tarifs
    annee_active = AnneeSportive.objects.filter(ligue=ligue, statut='ACTIVE').first()
    tarifs_actifs = []
    nb_tarifs = 0
    if annee_active:
        tarifs_actifs = annee_active.tarifs.select_related('grade').order_by('grade__ordre')
        nb_tarifs = tarifs_actifs.count()

    contexte = {
        'ligue':               ligue,
        'nb_clubs_affilies':   clubs_qs.filter(statut_club='AFFILIE').count(),
        'nb_clubs_en_attente': clubs_qs.filter(statut_club='EN_ATTENTE').count(),
        'nb_licencies':        nb_licencies,
        'nb_demandes_attente': demandes_qs.count(),
        'demandes_en_attente': demandes_qs.select_related('club', 'annee_sportive').order_by('-date_demande')[:5],
        'derniere_session':    derniere_session,
        'clubs_resume':        clubs_resume,
        'nb_grades':           Grade.objects.filter(ligue=ligue).count(),
        'annee_active':        annee_active,
        'tarifs_actifs':       tarifs_actifs,
        'nb_tarifs':           nb_tarifs,
    }
    return render(request, 'accounts/dashboard_ligue.html', contexte)


@login_required
def dashboard_club(request):
    from apps.practitioners.models import Pratiquant
    from apps.exams.models import SessionExamen, Inscription
    from django.db.models import Count, Q

    club = getattr(request.user, 'club', None)
    if not club:
        messages.warning(request, "Votre compte n'est rattaché à aucun club.")
        return render(request, 'accounts/dashboard_club.html', {'club': None})

    # Sessions avec le nombre de pratiquants du club inscrits
    sessions_avec_inscrits = (
        SessionExamen.objects
        .filter(inscriptions__pratiquant__club=club)
        .annotate(nb_inscrits=Count('inscriptions', filter=Q(inscriptions__pratiquant__club=club)))
        .order_by('-date_examen')
    )

    contexte = {
        'club':                 club,
        'nb_pratiquants':       Pratiquant.objects.filter(club=club, actif=True).count(),
        'nb_inactifs':          Pratiquant.objects.filter(club=club, actif=False).count(),
        'derniers_pratiquants': Pratiquant.objects.filter(club=club).select_related('grade_actuel').order_by('-date_inscription')[:5],
        'sessions_avec_inscrits': sessions_avec_inscrits,
    }
    return render(request, 'accounts/dashboard_club.html', contexte)


@login_required
def dashboard_financier(request):
    from apps.payments.models import PaiementExamen
    ligue = request.user.ligue
    qs = PaiementExamen.objects.filter(session__annee_sportive__ligue=ligue) if ligue else PaiementExamen.objects.none()
    contexte = {
        'nb_en_attente': qs.filter(statut='EN_ATTENTE').count(),
        'nb_valides':    qs.filter(statut='VALIDE').count(),
        'nb_rejetes':    qs.filter(statut='REJETE').count(),
        'derniers_en_attente': qs.filter(statut='EN_ATTENTE').select_related('club', 'session').order_by('-date_soumission')[:5],
    }
    return render(request, 'accounts/dashboard_financier.html', contexte)


@login_required
def dashboard_jury(request):
    from apps.exams.models import AffectationJury, SessionExamen
    affectations = (
        AffectationJury.objects
        .filter(jury=request.user)
        .select_related('session', 'session__annee_sportive')
        .order_by('-session__date_examen')
    )
    sessions_en_cours = [a.session for a in affectations if a.session.statut == 'EN_COURS']
    return render(request, 'accounts/dashboard_jury.html', {
        'affectations':    affectations,
        'sessions_en_cours': sessions_en_cours,
    })


# ── Gestion des utilisateurs (Super Admin) ────────────────────────────

@super_admin_requis
def liste_utilisateurs(request):
    utilisateurs = Utilisateur.objects.filter(
        is_superuser=False
    ).prefetch_related('roles').order_by('last_name', 'first_name')
    return render(request, 'super_admin/utilisateurs_liste.html', {
        'utilisateurs': utilisateurs
    })


@super_admin_requis
def creer_utilisateur(request):
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte utilisateur créé avec succès.")
            return redirect('accounts:liste_utilisateurs')
    else:
        form = UtilisateurCreationForm()
    return render(request, 'super_admin/utilisateur_form.html', {
        'form': form, 'titre': 'Créer un utilisateur'
    })


@super_admin_requis
def modifier_utilisateur(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if request.method == 'POST':
        form = UtilisateurModificationForm(request.POST, request.FILES, instance=utilisateur)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte modifié avec succès.")
            return redirect('accounts:liste_utilisateurs')
    else:
        form = UtilisateurModificationForm(instance=utilisateur)
    return render(request, 'super_admin/utilisateur_form.html', {
        'form': form, 'titre': 'Modifier l\'utilisateur', 'utilisateur': utilisateur
    })


@super_admin_requis
def gerer_roles(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if request.method == 'POST':
        form = RolesForm(request.POST)
        if form.is_valid():
            # Supprime tous les rôles et réattribue
            UtilisateurRole.objects.filter(utilisateur=utilisateur).delete()
            for role in form.cleaned_data['roles']:
                UtilisateurRole.objects.create(utilisateur=utilisateur, role=role)
            messages.success(request, "Rôles mis à jour avec succès.")
            return redirect('accounts:liste_utilisateurs')
    else:
        roles_actuels = utilisateur.roles.all()
        form = RolesForm(initial={'roles': roles_actuels})
    return render(request, 'super_admin/gerer_roles.html', {
        'form': form, 'utilisateur': utilisateur
    })


@super_admin_requis
def toggle_statut_utilisateur(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if utilisateur.statut_compte:
        utilisateur.statut_compte = False
        messages.warning(request, f"Compte de {utilisateur.get_full_name()} désactivé.")
    else:
        utilisateur.statut_compte = True
        messages.success(request, f"Compte de {utilisateur.get_full_name()} réactivé.")
    utilisateur.save()
    return redirect('accounts:liste_utilisateurs')


@super_admin_requis
def supprimer_utilisateur(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if utilisateur.is_superuser:
        messages.error(request, "Impossible de supprimer un super administrateur système.")
        return redirect('accounts:liste_utilisateurs')

    # Club dont cet utilisateur est gestionnaire (OneToOne inverse)
    club_gere = None
    try:
        club_gere = utilisateur.club
    except Exception:
        pass

    if request.method == 'POST':
        nom = utilisateur.get_full_name() or utilisateur.username
        # Détacher du club avant suppression pour éviter ProtectedError
        if club_gere:
            club_gere.utilisateur = None
            club_gere.save()
        utilisateur.delete()
        messages.success(request, f"Utilisateur « {nom} » supprimé.")
        return redirect('accounts:liste_utilisateurs')
    return render(request, 'super_admin/confirmer_suppression_utilisateur.html', {
        'utilisateur': utilisateur,
        'club_gere':   club_gere,
    })
