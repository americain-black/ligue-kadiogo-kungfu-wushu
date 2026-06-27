from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from .models import PaiementExamen
from .forms import PaiementExamenForm, RejetPaiementForm
from apps.exams.models import SessionExamen, Inscription


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

    nb_inscrits = Inscription.objects.filter(session=session, pratiquant__club=club).count()
    if nb_inscrits == 0:
        messages.error(request, "Inscrivez d'abord vos pratiquants avant de soumettre un paiement.")
        return redirect('exams:club_inscriptions', session_pk=session_pk)

    montant_attendu = (
        Inscription.objects
        .filter(session=session, pratiquant__club=club)
        .aggregate(total=Sum('montant'))['total'] or 0
    )

    paiement_existant = PaiementExamen.objects.filter(club=club, session=session).first()

    if paiement_existant and paiement_existant.statut == 'VALIDE':
        messages.info(request, "Le paiement pour cette session est déjà validé.")
        return redirect('exams:club_inscriptions', session_pk=session_pk)

    if paiement_existant and paiement_existant.statut == 'EN_ATTENTE':
        messages.info(request, "Votre preuve de paiement est déjà en cours de vérification.")
        return redirect('exams:club_inscriptions', session_pk=session_pk)

    if request.method == 'POST':
        form = PaiementExamenForm(request.POST, request.FILES)
        if form.is_valid():
            if paiement_existant:
                # Resoumission après rejet
                paiement_existant.montant_paye    = form.cleaned_data['montant_paye']
                paiement_existant.reference       = form.cleaned_data['reference']
                paiement_existant.fichier_preuve  = form.cleaned_data['fichier_preuve']
                paiement_existant.montant_attendu = montant_attendu
                paiement_existant.statut          = 'EN_ATTENTE'
                paiement_existant.motif_rejet     = ''
                paiement_existant.valide_par      = None
                paiement_existant.date_validation = None
                paiement_existant.save()
                messages.success(request, "Preuve de paiement resoumise avec succès.")
            else:
                paiement = form.save(commit=False)
                paiement.club            = club
                paiement.session         = session
                paiement.montant_attendu = montant_attendu
                paiement.save()
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
        'montant_attendu': montant_attendu,
        'nb_inscrits':     nb_inscrits,
        'paiement':        paiement_existant,
    })


# ── Vues GEST_FINANCIER ───────────────────────────────────────────────────────

@gest_financier_requis
def liste_paiements_examen(request):
    statut_filtre = request.GET.get('statut', 'EN_ATTENTE')
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
    if request.method == 'POST':
        paiement.valider(request.user)
        messages.success(
            request,
            f"Paiement de « {paiement.club.nom_club} » validé. "
            f"Les inscriptions passent en « Paiement validé »."
        )
        return redirect('payments:liste_paiements_examen')
    return render(request, 'payments/confirmer_valider_paiement.html', {
        'paiement': paiement,
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
            paiement.rejeter(request.user, motif=form.cleaned_data['motif'])
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
