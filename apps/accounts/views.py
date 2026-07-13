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
    nb_ligues_actives = Ligue.objects.filter(statut='ACTIVE').count()
    nb_ligues_total   = Ligue.objects.count()
    nb_utilisateurs   = Utilisateur.objects.filter(is_superuser=False).count()
    nb_actifs         = Utilisateur.objects.filter(statut_compte=True, is_superuser=False).count()
    contexte = {
        'nb_ligues_actives':    nb_ligues_actives,
        'nb_ligues_inactives':  nb_ligues_total - nb_ligues_actives,
        'nb_ligues_total':      nb_ligues_total,
        'nb_utilisateurs':      nb_utilisateurs,
        'nb_actifs':            nb_actifs,
        'nb_inactifs':          nb_utilisateurs - nb_actifs,
        'dernieres_ligues':     Ligue.objects.order_by('-date_creation')[:3],
        'derniers_utilisateurs': Utilisateur.objects.filter(is_superuser=False).order_by('-date_joined')[:3],
    }
    return render(request, 'accounts/dashboard_super_admin.html', contexte)


@login_required
def dashboard_ligue(request):
    from apps.clubs.models import Club, DemandeAffiliation
    from apps.exams.models import SessionExamen, Inscription
    from django.db.models import Count, Q

    ligue = request.user.ligue

    if not ligue:
        messages.warning(request, "Votre compte n'est rattaché à aucune ligue.")
        return render(request, 'accounts/dashboard_ligue.html', {'ligue': None})

    clubs_qs    = Club.objects.filter(ligue=ligue)
    demandes_qs = DemandeAffiliation.objects.filter(
        club__ligue=ligue,
        statut_affiliation='EN_ATTENTE_VALID_LIGUE'
    )

    # Statistiques globales
    nb_clubs_total      = clubs_qs.count()
    nb_clubs_affilies   = clubs_qs.filter(statut_club='AFFILIE').count()
    nb_clubs_en_attente = clubs_qs.filter(statut_club='EN_ATTENTE').count()
    nb_demandes_attente = demandes_qs.count()

    # Toutes les sessions de la ligue, avec stats d'inscription
    sessions_qs = (
        SessionExamen.objects
        .filter(annee_sportive__ligue=ligue)
        .select_related('annee_sportive')
        .order_by('-date_examen')
    )
    sessions_list = []
    nb_licencies_total = 0
    for s in sessions_qs:
        qs_i = Inscription.objects.filter(session=s)
        nb_aut = qs_i.filter(statut='AUTORISE').count()
        nb_licencies_total += nb_aut
        sessions_list.append({
            'session':       s,
            'nb_inscrits':   qs_i.count(),
            'nb_autorises':  nb_aut,
            'nb_exclus':     qs_i.filter(statut='EXCLU').count(),
            'nb_en_attente': qs_i.filter(statut='EN_ATTENTE_PAIEMENT').count(),
        })

    nb_sessions_total  = len(sessions_list)
    nb_sessions_actives = sessions_qs.exclude(
        statut__in=['CLOTUREE', 'RESULTATS_PUBLIES']
    ).count()

    contexte = {
        'ligue':               ligue,
        'nb_clubs_total':      nb_clubs_total,
        'nb_clubs_affilies':   nb_clubs_affilies,
        'nb_clubs_en_attente': nb_clubs_en_attente,
        'nb_demandes_attente': nb_demandes_attente,
        'demandes_en_attente': demandes_qs.select_related('club', 'annee_sportive').order_by('-date_demande')[:5],
        'nb_licencies_total':  nb_licencies_total,
        'nb_sessions_total':   nb_sessions_total,
        'nb_sessions_actives': nb_sessions_actives,
        'sessions_list':       sessions_list,
    }
    return render(request, 'accounts/dashboard_ligue.html', contexte)


@login_required
def dashboard_club(request):
    from apps.practitioners.models import Pratiquant
    from apps.exams.models import SessionExamen, Inscription
    from django.db.models import Count, Q

    from apps.clubs.models import DemandeAffiliation

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

    # Sessions actives de la ligue — pour le ticker d'information
    _MESSAGES = {
        'EN_PREPARATION':     "est en cours de préparation par la ligue. Vous serez informé dès que les inscriptions seront ouvertes.",
        'INSCRIPTIONS_OUVERTES': "Les inscriptions sont ouvertes. Inscrivez vos pratiquants et soumettez votre preuve de paiement avant la date de clôture.",
        'INSCRIPTIONS_CLOSES':   "Les inscriptions sont closes. Vous ne pouvez plus inscrire de nouveaux pratiquants, mais vous pouvez encore régulariser votre paiement si nécessaire.",
        'EN_COURS':           "L'examen est en cours. Assurez-vous que le paiement de vos pratiquants est bien validé.",
        'CLOTUREE':           "L'examen est terminé. Les résultats sont en cours de traitement par la ligue.",
    }
    _COULEURS = {
        'EN_PREPARATION':     'ticker-gris',
        'INSCRIPTIONS_OUVERTES': 'ticker-vert',
        'INSCRIPTIONS_CLOSES':   'ticker-orange',
        'EN_COURS':           'ticker-bleu',
        'CLOTUREE':           'ticker-sombre',
    }
    ticker_sessions = []
    if club.ligue:
        qs_ticker = (
            SessionExamen.objects
            .filter(annee_sportive__ligue=club.ligue)
            .exclude(statut='RESULTATS_PUBLIES')
            .order_by('date_examen')
        )
        for s in qs_ticker:
            ticker_sessions.append({
                'titre':   s.titre,
                'statut':  s.statut,
                'message': _MESSAGES.get(s.statut, ''),
                'couleur': _COULEURS.get(s.statut, 'ticker-gris'),
            })

    annee_active = None
    if club.ligue:
        from apps.exams.models import AnneeSportive
        annee_active = AnneeSportive.objects.filter(ligue=club.ligue, statut='ACTIVE').first()
    demande_affiliation = (
        DemandeAffiliation.objects.filter(club=club, annee_sportive=annee_active).first()
        if annee_active else None
    )

    contexte = {
        'club':                   club,
        'nb_pratiquants':         Pratiquant.objects.filter(club=club, actif=True).count(),
        'nb_inactifs':            Pratiquant.objects.filter(club=club, actif=False).count(),
        'derniers_pratiquants':   Pratiquant.objects.filter(club=club).select_related('grade_actuel').order_by('-date_inscription')[:5],
        'sessions_avec_inscrits': sessions_avec_inscrits,
        'ticker_sessions':        ticker_sessions,
        'demande_affiliation':    demande_affiliation,
    }
    return render(request, 'accounts/dashboard_club.html', contexte)


@login_required
def dashboard_financier(request):
    from apps.payments.models import PaiementExamen, PaiementAffiliation
    ligue = request.user.ligue
    qs = PaiementExamen.objects.filter(session__annee_sportive__ligue=ligue) if ligue else PaiementExamen.objects.none()
    qs_aff = (
        PaiementAffiliation.objects.filter(demande__club__ligue=ligue)
        if ligue else PaiementAffiliation.objects.none()
    )
    contexte = {
        'nb_en_attente': qs.filter(statut='EN_ATTENTE').count(),
        'nb_valides':    qs.filter(statut='VALIDE').count(),
        'nb_rejetes':    qs.filter(statut='REJETE').count(),
        'derniers_en_attente': qs.filter(statut='EN_ATTENTE').select_related('club', 'session').order_by('-date_soumission')[:5],
        'nb_en_attente_affiliation': qs_aff.filter(statut='EN_ATTENTE').count(),
        'nb_valides_affiliation':    qs_aff.filter(statut='VALIDE').count(),
        'nb_rejetes_affiliation':    qs_aff.filter(statut='REJETE').count(),
        'derniers_en_attente_affiliation': qs_aff.filter(statut='EN_ATTENTE').select_related('demande__club', 'demande__annee_sportive').order_by('-date_soumission')[:5],
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
    from apps.exams.models import AffectationJury
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

    # Affectations jury : bloquent la suppression (AffectationJury.jury est PROTECT)
    affectations_jury = AffectationJury.objects.filter(jury=utilisateur).select_related('session')

    if request.method == 'POST':
        if affectations_jury.exists():
            sessions = ', '.join(a.session.titre for a in affectations_jury)
            messages.error(
                request,
                f"Impossible de supprimer « {utilisateur.get_full_name() or utilisateur.username} » : "
                f"encore affecté(e) comme jury sur : {sessions}. Retirez d'abord ces affectations."
            )
            return redirect('accounts:supprimer_utilisateur', pk=pk)

        nom = utilisateur.get_full_name() or utilisateur.username
        # Détacher du club avant suppression pour éviter ProtectedError
        if club_gere:
            club_gere.utilisateur = None
            club_gere.save()
        utilisateur.delete()
        messages.success(request, f"Utilisateur « {nom} » supprimé.")
        return redirect('accounts:liste_utilisateurs')
    return render(request, 'super_admin/confirmer_suppression_utilisateur.html', {
        'utilisateur':       utilisateur,
        'club_gere':         club_gere,
        'affectations_jury': affectations_jury,
    })
