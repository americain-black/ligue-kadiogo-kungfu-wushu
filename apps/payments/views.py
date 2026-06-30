from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from .models import PaiementExamen, HistoriquePaiementExamen
from .forms import PaiementExamenForm, RejetPaiementForm, InsuffisantPaiementForm
from apps.exams.models import SessionExamen, Inscription, ParametresExamen


# ── Décorateurs ───────────────────────────────────────────────────────────────

def gest_financier_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_financier()):
            messages.error(request, "Accès réservé au Gestionnaire Financier.")
            return redirect('accounts:tableau_de_bord')
        if not request.user.ligue and not request.user.is_superuser:
            messages.error(request, "Votre compte n'est rattaché à aucune ligue.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


def gest_club_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_club()):
            messages.error(request, "Accès réservé au Gestionnaire de Club.")
            return redirect('accounts:tableau_de_bord')
        try:
            _ = request.user.club
        except Exception:
            messages.error(request, "Votre compte n'est rattaché à aucun club.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Vues GEST_CLUB — Soumettre preuve ────────────────────────────────────────

@gest_club_requis
def soumettre_paiement_examen(request, session_pk):
    club    = request.user.club
    session = get_object_or_404(
        SessionExamen, pk=session_pk,
        annee_sportive__ligue=club.ligue,
    )

    statuts_autorises = ['INSCRIPTIONS_OUVERTES', 'INSCRIPTIONS_CLOSES', 'EN_COURS']
    if session.statut not in statuts_autorises:
        messages.error(request, "Vous ne pouvez pas soumettre de paiement pour cette session.")
        return redirect('exams:club_inscriptions', session_pk=session_pk)

    # Compter uniquement les inscriptions EN_ATTENTE_PAIEMENT (non encore couvertes)
    inscriptions_en_attente = Inscription.objects.filter(
        session=session, pratiquant__club=club, statut='EN_ATTENTE_PAIEMENT'
    )
    nb_en_attente = inscriptions_en_attente.count()

    if nb_en_attente == 0:
        messages.info(request, "Tous vos pratiquants inscrits ont déjà un paiement soumis ou validé.")
        return redirect('exams:club_inscriptions', session_pk=session_pk)

    # Montant brut (somme des tarifs pour les inscriptions en attente)
    montant_brut = inscriptions_en_attente.aggregate(total=Sum('montant'))['total'] or Decimal('0')

    # Appliquer le pourcentage de la ligue
    params        = ParametresExamen.objects.filter(ligue=club.ligue).first()
    pourcentage   = params.pourcentage_ligue if params else Decimal('100')
    montant_attendu = (montant_brut * pourcentage / 100).quantize(Decimal('1'))

    # Bloquer si un paiement est déjà EN_ATTENTE de vérification
    paiement_en_attente = PaiementExamen.objects.filter(
        club=club, session=session, statut='EN_ATTENTE'
    ).first()
    if paiement_en_attente:
        messages.info(request, "Votre preuve de paiement est déjà en cours de vérification.")
        return redirect('exams:club_inscriptions', session_pk=session_pk)

    # Paiement le plus récent à retravailler : REJETE ou INSUFFISANT
    paiement_rejete = (
        PaiementExamen.objects
        .filter(club=club, session=session, statut__in=['REJETE', 'INSUFFISANT'])
        .order_by('-date_soumission')
        .first()
    )

    if request.method == 'POST':
        form = PaiementExamenForm(request.POST, request.FILES)
        if form.is_valid():
            if paiement_rejete:
                paiement_rejete.mode_paiement       = form.cleaned_data['mode_paiement']
                paiement_rejete.numero_expediteur   = form.cleaned_data['numero_expediteur']
                paiement_rejete.numero_beneficiaire = form.cleaned_data['numero_beneficiaire']
                paiement_rejete.montant_paye        = form.cleaned_data['montant_paye']
                paiement_rejete.reference           = form.cleaned_data['reference']
                paiement_rejete.fichier_preuve      = form.cleaned_data['fichier_preuve']
                paiement_rejete.montant_attendu     = montant_attendu
                paiement_rejete.statut              = 'EN_ATTENTE'
                paiement_rejete.motif_rejet         = ''
                paiement_rejete.valide_par          = None
                paiement_rejete.date_validation     = None
                paiement_rejete.save()
                HistoriquePaiementExamen.objects.create(
                    paiement=paiement_rejete, action='RESOUMIS',
                    acteur=request.user, montant=form.cleaned_data['montant_paye']
                )
                messages.success(request, "Preuve de paiement resoumise avec succès.")
            else:
                paiement = form.save(commit=False)
                paiement.club            = club
                paiement.session         = session
                paiement.montant_attendu = montant_attendu
                paiement.save()
                HistoriquePaiementExamen.objects.create(
                    paiement=paiement, action='SOUMIS',
                    acteur=request.user, montant=form.cleaned_data['montant_paye']
                )
                messages.success(
                    request,
                    "Preuve de paiement soumise. Le gestionnaire financier va la vérifier."
                )
            return redirect('exams:club_inscriptions', session_pk=session_pk)
    else:
        form = PaiementExamenForm()

    return render(request, 'payments/soumettre_paiement_examen.html', {
        'form':            form,
        'session':         session,
        'club':            club,
        'montant_brut':    montant_brut,
        'montant_attendu': montant_attendu,
        'pourcentage':     pourcentage,
        'nb_en_attente':   nb_en_attente,
        'paiement':        paiement_rejete,
        'params':          params,
    })


# ── Vues GEST_FINANCIER ───────────────────────────────────────────────────────

@gest_financier_requis
def liste_paiements_examen(request):
    statut_filtre = request.GET.get('statut', '')
    paiements = (
        PaiementExamen.objects
        .filter(session__annee_sportive__ligue=request.user.ligue)
        .select_related('club', 'session', 'valide_par')
        .order_by('-date_soumission')
    )
    if statut_filtre:
        paiements = paiements.filter(statut=statut_filtre)
    return render(request, 'payments/liste_paiements_examen.html', {
        'paiements':     paiements,
        'statut_filtre': statut_filtre,
        'statuts':       PaiementExamen.STATUT_CHOICES,
    })


@gest_financier_requis
def detail_paiement_examen(request, pk):
    paiement = get_object_or_404(
        PaiementExamen, pk=pk,
        session__annee_sportive__ligue=request.user.ligue
    )
    inscriptions = (
        Inscription.objects
        .filter(session=paiement.session, pratiquant__club=paiement.club)
        .select_related('pratiquant', 'grade_vise')
    )
    return render(request, 'payments/detail_paiement_examen.html', {
        'paiement':    paiement,
        'inscriptions': inscriptions,
    })


@gest_financier_requis
def valider_paiement_examen(request, pk):
    paiement = get_object_or_404(
        PaiementExamen, pk=pk,
        session__annee_sportive__ligue=request.user.ligue,
        statut='EN_ATTENTE'
    )
    inscriptions = (
        Inscription.objects
        .filter(session=paiement.session, pratiquant__club=paiement.club,
                statut='EN_ATTENTE_PAIEMENT')
        .select_related('pratiquant', 'grade_vise')
    )
    if request.method == 'POST':
        nb = inscriptions.count()
        paiement.valider(request.user)
        HistoriquePaiementExamen.objects.create(
            paiement=paiement, action='VALIDE',
            acteur=request.user, montant=paiement.montant_paye
        )
        messages.success(
            request,
            f"Paiement de « {paiement.club.nom_club} » validé. "
            f"{nb} inscription(s) passent en « Paiement validé »."
        )
        return redirect('payments:liste_paiements_examen')
    # Calcul pour affichage
    manque = max(Decimal('0'), paiement.montant_attendu - paiement.montant_paye)
    return render(request, 'payments/confirmer_valider_paiement.html', {
        'paiement':     paiement,
        'inscriptions': inscriptions,
        'manque':       manque,
    })


@gest_financier_requis
def insuffisant_paiement_examen(request, pk):
    paiement = get_object_or_404(
        PaiementExamen, pk=pk,
        session__annee_sportive__ligue=request.user.ligue,
        statut='EN_ATTENTE'
    )
    inscriptions = (
        Inscription.objects
        .filter(session=paiement.session, pratiquant__club=paiement.club,
                statut='EN_ATTENTE_PAIEMENT')
        .select_related('pratiquant', 'grade_vise')
    )
    manque = max(Decimal('0'), paiement.montant_attendu - paiement.montant_paye)
    session = paiement.session

    if request.method == 'POST':
        form = InsuffisantPaiementForm(request.POST)
        if form.is_valid():
            motif = form.cleaned_data['motif']
            paiement.valider_insuffisant(request.user, motif)
            HistoriquePaiementExamen.objects.create(
                paiement=paiement, action='INSUFFISANT',
                acteur=request.user, montant=paiement.montant_paye, motif=motif
            )
            date_limite = session.date_limite_paiement
            date_str = date_limite.strftime('%d/%m/%Y') if date_limite else "non définie"
            messages.warning(
                request,
                f"Paiement de « {paiement.club.nom_club} » marqué insuffisant. "
                f"Le club doit compléter ou régulariser avant le {date_str}."
            )
            return redirect('payments:liste_paiements_examen')
    else:
        montant_recu  = paiement.montant_paye
        montant_dû    = paiement.montant_attendu
        date_limite   = session.date_limite_paiement
        date_str      = date_limite.strftime('%d/%m/%Y') if date_limite else "non définie"
        motif_auto = (
            f"Montant reçu : {montant_recu:,.0f} FCFA — "
            f"Montant attendu : {montant_dû:,.0f} FCFA — "
            f"Manque : {manque:,.0f} FCFA. "
            f"Veuillez compléter le paiement ou retirer les pratiquants non couverts "
            f"avant le {date_str}."
        )
        form = InsuffisantPaiementForm(initial={'motif': motif_auto})
    return render(request, 'payments/insuffisant_paiement.html', {
        'form':         form,
        'paiement':     paiement,
        'inscriptions': inscriptions,
        'manque':       manque,
        'session':      session,
    })


@gest_financier_requis
def rejeter_paiement_examen(request, pk):
    paiement = get_object_or_404(
        PaiementExamen, pk=pk,
        session__annee_sportive__ligue=request.user.ligue,
        statut='EN_ATTENTE'
    )
    if request.method == 'POST':
        form = RejetPaiementForm(request.POST)
        if form.is_valid():
            motif = form.cleaned_data['motif']
            paiement.rejeter(request.user, motif=motif)
            HistoriquePaiementExamen.objects.create(
                paiement=paiement, action='REJETE',
                acteur=request.user, montant=paiement.montant_paye, motif=motif
            )
            messages.warning(
                request,
                f"Paiement de « {paiement.club.nom_club} » rejeté. Le club peut resoumettre une preuve."
            )
            return redirect('payments:liste_paiements_examen')
    else:
        form = RejetPaiementForm()
    return render(request, 'payments/rejeter_paiement_examen.html', {
        'form':    form,
        'paiement': paiement,
    })


@gest_financier_requis
def historique_paiements_examen(request):
    ligue = request.user.ligue
    session_pk = request.GET.get('session', '')
    club_pk    = request.GET.get('club', '')
    action_filtre = request.GET.get('action', '')

    historique = (
        HistoriquePaiementExamen.objects
        .filter(paiement__session__annee_sportive__ligue=ligue)
        .select_related('paiement__club', 'paiement__session', 'acteur')
        .order_by('-date_action')
    )
    if session_pk:
        historique = historique.filter(paiement__session_id=session_pk)
    if club_pk:
        historique = historique.filter(paiement__club_id=club_pk)
    if action_filtre:
        historique = historique.filter(action=action_filtre)

    from apps.exams.models import SessionExamen
    from apps.clubs.models import Club
    sessions = SessionExamen.objects.filter(annee_sportive__ligue=ligue).order_by('-date_examen')
    clubs    = Club.objects.filter(ligue=ligue).order_by('nom_club')

    return render(request, 'payments/historique_paiements.html', {
        'historique':     historique,
        'sessions':       sessions,
        'clubs':          clubs,
        'session_pk':     session_pk,
        'club_pk':        club_pk,
        'action_filtre':  action_filtre,
        'actions':        HistoriquePaiementExamen.ACTION_CHOICES,
    })
