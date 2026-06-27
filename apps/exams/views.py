from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db.models import Sum

from django.db import transaction
from .models import SessionExamen, AffectationJury, Inscription, AnneeSportive, TarifExamen, Rubrique, RubriqueGrade, OptionExamen, ModeleMatricule
from .forms import SessionExamenForm, MultiInscriptionForm, AffectationJuryForm, AnneeSportiveForm, TarifExamenForm, RubriqueForm, RubriqueGradeForm, OptionExamenForm, ModeleMatriculeForm
from apps.payments.models import PaiementExamen


# ── Décorateurs ───────────────────────────────────────────────────────────────

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


# ── Vues GEST_LIGUE — Années sportives ───────────────────────────────────────

@gest_ligue_requis
def liste_annees_sportives(request):
    annees = AnneeSportive.objects.filter(ligue=request.user.ligue).order_by('-date_debut')
    return render(request, 'exams/annees_sportives.html', {'annees': annees})


@gest_ligue_requis
def creer_annee_sportive(request):
    if request.method == 'POST':
        form = AnneeSportiveForm(request.POST)
        if form.is_valid():
            annee = form.save(commit=False)
            annee.ligue = request.user.ligue
            annee.save()
            messages.success(request, f"Année sportive « {annee.libelle} » créée.")
            return redirect('exams:annees_sportives')
    else:
        form = AnneeSportiveForm()
    return render(request, 'exams/annee_sportive_form.html', {
        'form':  form,
        'titre': "Créer une année sportive",
    })


@gest_ligue_requis
def modifier_annee_sportive(request, pk):
    annee = get_object_or_404(AnneeSportive, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        form = AnneeSportiveForm(request.POST, instance=annee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Année sportive « {annee.libelle} » modifiée.")
            return redirect('exams:annees_sportives')
    else:
        form = AnneeSportiveForm(instance=annee)
    return render(request, 'exams/annee_sportive_form.html', {
        'form':  form,
        'titre': f"Modifier — {annee.libelle}",
        'annee': annee,
    })


@gest_ligue_requis
def cloturer_annee_sportive(request, pk):
    annee = get_object_or_404(AnneeSportive, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        if annee.statut == 'ACTIVE':
            annee.statut = 'CLOTUREE'
            annee.save()
            messages.success(request, f"Année sportive « {annee.libelle} » clôturée.")
        else:
            messages.error(request, "Cette année sportive est déjà clôturée.")
    return redirect('exams:annees_sportives')


@gest_ligue_requis
def supprimer_annee_sportive(request, pk):
    from apps.clubs.models import DemandeAffiliation
    annee = get_object_or_404(AnneeSportive, pk=pk, ligue=request.user.ligue)
    nb_sessions = annee.sessions.count()
    nb_demandes = DemandeAffiliation.objects.filter(annee_sportive=annee).count()
    if request.method == 'POST':
        libelle = annee.libelle
        with transaction.atomic():
            for session in annee.sessions.all():
                Inscription.objects.filter(session=session).delete()
                PaiementExamen.objects.filter(session=session).delete()
                session.affectations_jury.all().delete()
            TarifExamen.objects.filter(annee_sportive=annee).delete()
            annee.sessions.all().delete()
            DemandeAffiliation.objects.filter(annee_sportive=annee).delete()
            annee.delete()
        messages.success(request, f"Année sportive « {libelle} » supprimée.")
        return redirect('exams:annees_sportives')
    return render(request, 'exams/confirmer_suppression_annee.html', {
        'annee':       annee,
        'nb_sessions': nb_sessions,
        'nb_demandes': nb_demandes,
    })


# ── Vues GEST_LIGUE — Tarifs d'examen ────────────────────────────────────────

@gest_ligue_requis
def liste_tarifs(request, annee_pk):
    annee = get_object_or_404(AnneeSportive, pk=annee_pk, ligue=request.user.ligue)
    ligue = request.user.ligue
    tarifs = annee.tarifs.select_related('grade').order_by('grade__ordre')

    if request.method == 'POST':
        form = TarifExamenForm(request.POST, ligue=ligue, annee=annee)
        if form.is_valid():
            tarif = form.save(commit=False)
            tarif.annee_sportive = annee
            tarif.save()
            messages.success(request, f"Tarif « {tarif.grade.nom} » : {tarif.montant} FCFA ajouté.")
            return redirect('exams:tarifs', annee_pk=annee.pk)
    else:
        form = TarifExamenForm(ligue=ligue, annee=annee)

    return render(request, 'exams/tarifs.html', {
        'annee':  annee,
        'tarifs': tarifs,
        'form':   form,
    })


@gest_ligue_requis
def modifier_tarif(request, pk):
    tarif = get_object_or_404(TarifExamen, pk=pk, annee_sportive__ligue=request.user.ligue)
    annee = tarif.annee_sportive
    ligue = request.user.ligue
    if request.method == 'POST':
        form = TarifExamenForm(request.POST, instance=tarif, ligue=ligue, annee=annee)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarif modifié.")
            return redirect('exams:tarifs', annee_pk=annee.pk)
    else:
        form = TarifExamenForm(instance=tarif, ligue=ligue, annee=annee)
    return render(request, 'exams/tarifs.html', {
        'annee':        annee,
        'tarifs':       annee.tarifs.select_related('grade').order_by('grade__ordre'),
        'form':         form,
        'tarif_en_edition': tarif,
    })


@gest_ligue_requis
def supprimer_tarif(request, pk):
    tarif = get_object_or_404(TarifExamen, pk=pk, annee_sportive__ligue=request.user.ligue)
    annee = tarif.annee_sportive
    if request.method == 'POST':
        nom = tarif.grade.nom
        tarif.delete()
        messages.success(request, f"Tarif « {nom} » supprimé.")
    return redirect('exams:tarifs', annee_pk=annee.pk)


# ── Vues GEST_LIGUE — Rubriques / Épreuves ───────────────────────────────────

@gest_ligue_requis
def liste_rubriques(request):
    ligue = request.user.ligue
    rubriques = Rubrique.objects.all().order_by('nom')

    if request.method == 'POST':
        form = RubriqueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Rubrique « {form.cleaned_data['nom']} » créée.")
            return redirect('exams:rubriques')
    else:
        form = RubriqueForm()

    return render(request, 'exams/rubriques.html', {
        'rubriques': rubriques,
        'form':      form,
        'ligue':     ligue,
    })


@gest_ligue_requis
def modifier_rubrique(request, pk):
    rubrique = get_object_or_404(Rubrique, pk=pk)
    if request.method == 'POST':
        form = RubriqueForm(request.POST, instance=rubrique)
        if form.is_valid():
            form.save()
            messages.success(request, f"Rubrique « {rubrique.nom} » modifiée.")
            return redirect('exams:rubriques')
    else:
        form = RubriqueForm(instance=rubrique)

    rubriques = Rubrique.objects.all().order_by('nom')
    return render(request, 'exams/rubriques.html', {
        'rubriques':        rubriques,
        'form':             form,
        'rubrique_en_edition': rubrique,
        'ligue':            request.user.ligue,
    })


@gest_ligue_requis
def toggle_actif_rubrique(request, pk):
    rubrique = get_object_or_404(Rubrique, pk=pk)
    if request.method == 'POST':
        rubrique.actif = not rubrique.actif
        rubrique.save()
        etat = "activée" if rubrique.actif else "désactivée"
        messages.success(request, f"Rubrique « {rubrique.nom} » {etat}.")
    return redirect('exams:rubriques')


@gest_ligue_requis
def supprimer_rubrique(request, pk):
    rubrique = get_object_or_404(Rubrique, pk=pk)
    if request.method == 'POST':
        nb_assoc = rubrique.rubrique_grades.count()
        if nb_assoc:
            messages.error(
                request,
                f"Impossible de supprimer « {rubrique.nom} » : elle est configurée pour {nb_assoc} grade(s). "
                "Retirez-la de tous les grades d'abord."
            )
        else:
            nom = rubrique.nom
            rubrique.delete()
            messages.success(request, f"Rubrique « {nom} » supprimée.")
    return redirect('exams:rubriques')


@gest_ligue_requis
def config_rubrique_grades(request, pk):
    rubrique = get_object_or_404(Rubrique, pk=pk)
    ligue    = request.user.ligue
    assocs   = rubrique.rubrique_grades.select_related('grade').order_by('grade__ordre')

    if request.method == 'POST':
        form = RubriqueGradeForm(request.POST, ligue=ligue, rubrique=rubrique)
        if form.is_valid():
            rg = form.save(commit=False)
            rg.rubrique = rubrique
            rg.save()
            messages.success(
                request,
                f"Grade « {rg.grade.nom} » associé à « {rubrique.nom} » (coeff {rg.coefficient})."
            )
            return redirect('exams:config_rubrique_grades', pk=pk)
    else:
        form = RubriqueGradeForm(ligue=ligue, rubrique=rubrique)

    return render(request, 'exams/rubrique_config.html', {
        'rubrique': rubrique,
        'assocs':   assocs,
        'form':     form,
    })


@gest_ligue_requis
def modifier_rubrique_grade(request, pk):
    rg       = get_object_or_404(RubriqueGrade, pk=pk)
    rubrique = rg.rubrique
    ligue    = request.user.ligue

    if request.method == 'POST':
        form = RubriqueGradeForm(request.POST, instance=rg, ligue=ligue, rubrique=rubrique)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuration mise à jour.")
            return redirect('exams:config_rubrique_grades', pk=rubrique.pk)
    else:
        form = RubriqueGradeForm(instance=rg, ligue=ligue, rubrique=rubrique)

    assocs = rubrique.rubrique_grades.select_related('grade').order_by('grade__ordre')
    return render(request, 'exams/rubrique_config.html', {
        'rubrique':   rubrique,
        'assocs':     assocs,
        'form':       form,
        'rg_en_edition': rg,
    })


@gest_ligue_requis
def toggle_actif_rubrique_grade(request, pk):
    rg = get_object_or_404(RubriqueGrade, pk=pk)
    if request.method == 'POST':
        rg.actif = not rg.actif
        rg.save()
        etat = "activée" if rg.actif else "désactivée"
        messages.success(request, f"Épreuve « {rg.rubrique.nom} » pour « {rg.grade.nom} » {etat}.")
    return redirect('exams:config_rubrique_grades', pk=rg.rubrique.pk)


@gest_ligue_requis
def supprimer_rubrique_grade(request, pk):
    rg = get_object_or_404(RubriqueGrade, pk=pk)
    rubrique_pk = rg.rubrique.pk
    if request.method == 'POST':
        nom = f"{rg.rubrique.nom} — {rg.grade.nom}"
        rg.delete()
        messages.success(request, f"Association « {nom} » supprimée.")
    return redirect('exams:config_rubrique_grades', pk=rubrique_pk)


# ── Vues GEST_LIGUE — Options d'examen ───────────────────────────────────────

@gest_ligue_requis
def liste_options(request):
    ligue   = request.user.ligue
    options = OptionExamen.objects.filter(ligue=ligue).order_by('nom')

    if request.method == 'POST':
        form = OptionExamenForm(request.POST)
        if form.is_valid():
            opt = form.save(commit=False)
            opt.ligue = ligue
            opt.save()
            messages.success(request, f"Option « {opt.nom} » créée.")
            return redirect('exams:options')
    else:
        form = OptionExamenForm()

    return render(request, 'exams/options.html', {
        'options': options,
        'form':    form,
    })


@gest_ligue_requis
def modifier_option(request, pk):
    opt   = get_object_or_404(OptionExamen, pk=pk, ligue=request.user.ligue)
    ligue = request.user.ligue

    if request.method == 'POST':
        form = OptionExamenForm(request.POST, instance=opt)
        if form.is_valid():
            form.save()
            messages.success(request, f"Option « {opt.nom} » modifiée.")
            return redirect('exams:options')
    else:
        form = OptionExamenForm(instance=opt)

    options = OptionExamen.objects.filter(ligue=ligue).order_by('nom')
    return render(request, 'exams/options.html', {
        'options':        options,
        'form':           form,
        'option_en_edition': opt,
    })


@gest_ligue_requis
def toggle_actif_option(request, pk):
    opt = get_object_or_404(OptionExamen, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        opt.actif = not opt.actif
        opt.save()
        etat = "activée" if opt.actif else "désactivée"
        messages.success(request, f"Option « {opt.nom} » {etat}.")
    return redirect('exams:options')


@gest_ligue_requis
def supprimer_option(request, pk):
    opt = get_object_or_404(OptionExamen, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        nb = opt.inscriptions.count()
        if nb:
            messages.error(request, f"Impossible : « {opt.nom} » est utilisée dans {nb} inscription(s).")
        else:
            nom = opt.nom
            opt.delete()
            messages.success(request, f"Option « {nom} » supprimée.")
    return redirect('exams:options')


# ── Vues GEST_LIGUE — Modèle de matricule ────────────────────────────────────

@gest_ligue_requis
def gerer_modele_matricule(request):
    ligue   = request.user.ligue
    modele  = ModeleMatricule.objects.filter(ligue=ligue).first()

    if request.method == 'POST':
        form = ModeleMatriculeForm(request.POST, instance=modele)
        if form.is_valid():
            m = form.save(commit=False)
            m.ligue = ligue
            m.save()
            messages.success(request, f"Modèle de matricule « {m.prefixe} » enregistré.")
            return redirect('exams:modele_matricule')
    else:
        form = ModeleMatriculeForm(instance=modele)

    # Aperçu du prochain matricule
    from datetime import date
    annee_courante = date.today().year
    prochain = None
    if modele:
        seq = modele.derniere_sequence + 1
        prochain = f"{modele.prefixe}{str(annee_courante)[-2:]}{seq:04d}"

    return render(request, 'exams/modele_matricule.html', {
        'modele':   modele,
        'form':     form,
        'prochain': prochain,
    })


@gest_ligue_requis
def supprimer_modele_matricule(request):
    ligue  = request.user.ligue
    modele = get_object_or_404(ModeleMatricule, ligue=ligue)
    if request.method == 'POST':
        prefixe = modele.prefixe
        modele.delete()
        messages.success(request, f"Modèle « {prefixe} » supprimé. Les matricules attribués sont conservés.")
    return redirect('exams:modele_matricule')


# ── Vues GEST_LIGUE — Sessions ────────────────────────────────────────────────

@gest_ligue_requis
def liste_sessions(request):
    sessions = (
        SessionExamen.objects
        .filter(annee_sportive__ligue=request.user.ligue)
        .select_related('annee_sportive')
        .order_by('-date_examen')
    )
    statut_filtre = request.GET.get('statut', '')
    if statut_filtre:
        sessions = sessions.filter(statut=statut_filtre)
    return render(request, 'exams/sessions_liste.html', {
        'sessions':      sessions,
        'statut_filtre': statut_filtre,
        'statuts':       SessionExamen.STATUT_CHOICES,
    })


@gest_ligue_requis
def creer_session(request):
    if request.method == 'POST':
        form = SessionExamenForm(request.POST, ligue=request.user.ligue)
        if form.is_valid():
            session = form.save()
            messages.success(request, f"Session « {session.titre} » créée.")
            return redirect('exams:detail', pk=session.pk)
    else:
        form = SessionExamenForm(ligue=request.user.ligue)
    return render(request, 'exams/session_form.html', {
        'form':  form,
        'titre': "Créer une session d'examen",
    })


@gest_ligue_requis
def modifier_session(request, pk):
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    if session.statut != 'EN_PREPARATION':
        messages.error(request, "Seules les sessions en préparation peuvent être modifiées.")
        return redirect('exams:detail', pk=pk)
    if request.method == 'POST':
        form = SessionExamenForm(request.POST, instance=session, ligue=request.user.ligue)
        if form.is_valid():
            form.save()
            messages.success(request, "Session modifiée.")
            return redirect('exams:detail', pk=pk)
    else:
        form = SessionExamenForm(instance=session, ligue=request.user.ligue)
    return render(request, 'exams/session_form.html', {
        'form':    form,
        'titre':   f"Modifier — {session.titre}",
        'session': session,
    })


@gest_ligue_requis
def detail_session(request, pk):
    from apps.payments.models import PaiementExamen
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    inscriptions = (
        session.inscriptions
        .select_related('pratiquant__club', 'grade_vise')
        .order_by('pratiquant__club__nom_club', 'pratiquant__nom', 'pratiquant__prenom')
    )
    affectations = session.affectations_jury.select_related('jury').order_by('date_affectation')
    jury_form    = AffectationJuryForm(session=session, ligue=request.user.ligue)

    # Regrouper par club pour afficher statut paiement et bouton valider liste
    clubs_dict = {}
    for insc in inscriptions:
        club = insc.pratiquant.club
        if club.pk not in clubs_dict:
            clubs_dict[club.pk] = {
                'club':          club,
                'inscriptions':  [],
                'montant_total': 0,
                'paiement':      None,
            }
        clubs_dict[club.pk]['inscriptions'].append(insc)
        clubs_dict[club.pk]['montant_total'] += insc.montant or 0

    paiements = PaiementExamen.objects.filter(session=session).select_related('club')
    paiements_par_club = {p.club_id: p for p in paiements}
    for club_pk, data in clubs_dict.items():
        data['paiement'] = paiements_par_club.get(club_pk)
        # Flag Python : évite {% break %} non supporté dans les templates Django
        data['a_paiement_valide_en_attente'] = any(
            i.statut == 'PAIEMENT_VALIDE' for i in data['inscriptions']
        )

    return render(request, 'exams/session_detail.html', {
        'session':      session,
        'clubs_data':   list(clubs_dict.values()),
        'affectations': affectations,
        'jury_form':    jury_form,
        'nb_inscrits':  inscriptions.count(),
    })


@gest_ligue_requis
def ouvrir_inscriptions(request, pk):
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    if request.method == 'POST':
        try:
            session.ouvrir_inscriptions()
            messages.success(request, "Les inscriptions sont maintenant ouvertes.")
        except ValidationError as e:
            messages.error(request, e.message)
        return redirect('exams:detail', pk=pk)
    return render(request, 'exams/session_confirmer_action.html', {
        'session':     session,
        'titre_action': "Ouvrir les inscriptions",
        'message':     f"Voulez-vous ouvrir les inscriptions pour « {session.titre} » ?",
        'btn_class':   'btn-success',
        'btn_label':   "Oui, ouvrir les inscriptions",
        'url_action':  reverse('exams:ouvrir_inscriptions', args=[pk]),
    })


@gest_ligue_requis
def cloturer_inscriptions(request, pk):
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    if request.method == 'POST':
        try:
            session.cloturer_inscriptions()
            messages.success(request, "Inscriptions clôturées.")
        except ValidationError as e:
            messages.error(request, e.message)
        return redirect('exams:detail', pk=pk)
    return render(request, 'exams/session_confirmer_action.html', {
        'session':      session,
        'titre_action': "Clôturer les inscriptions",
        'message':      f"Voulez-vous clôturer les inscriptions pour « {session.titre} » ? Les clubs ne pourront plus inscrire de pratiquants.",
        'btn_class':    'btn-warning',
        'btn_label':    "Oui, clôturer les inscriptions",
        'url_action':   reverse('exams:cloturer_inscriptions', args=[pk]),
    })


@gest_ligue_requis
def demarrer_session(request, pk):
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    if request.method == 'POST':
        if session.statut != 'INSCRIPTIONS_CLOSES':
            messages.error(request, "Les inscriptions doivent être closes avant de démarrer la session.")
            return redirect('exams:detail', pk=pk)
        session.statut = 'EN_COURS'
        session.save()
        messages.success(request, "Session démarrée.")
        return redirect('exams:detail', pk=pk)
    return render(request, 'exams/session_confirmer_action.html', {
        'session':      session,
        'titre_action': "Démarrer la session",
        'message':      f"Voulez-vous démarrer la session « {session.titre} » ? L'examen est en cours.",
        'btn_class':    'btn-primary',
        'btn_label':    "Oui, démarrer la session",
        'url_action':   reverse('exams:demarrer', args=[pk]),
    })


@gest_ligue_requis
def affecter_jury(request, pk):
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    if request.method == 'POST':
        form = AffectationJuryForm(request.POST, session=session, ligue=request.user.ligue)
        if form.is_valid():
            affectation = form.save(commit=False)
            affectation.session = session
            affectation.save()
            messages.success(request, f"{affectation.jury} affecté au jury.")
        else:
            messages.error(request, "Impossible d'affecter ce jury.")
    return redirect('exams:detail', pk=pk)


@gest_ligue_requis
def retirer_jury(request, pk):
    affectation = get_object_or_404(
        AffectationJury, pk=pk,
        session__annee_sportive__ligue=request.user.ligue
    )
    session_pk = affectation.session.pk
    if request.method == 'POST':
        nom = str(affectation.jury)
        affectation.delete()
        messages.success(request, f"{nom} retiré du jury.")
    return redirect('exams:detail', pk=session_pk)


# ── Vues GEST_CLUB — Inscriptions ─────────────────────────────────────────────

@gest_ligue_requis
def supprimer_session(request, pk):
    from apps.payments.models import PaiementExamen
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    if request.method == 'POST':
        if session.statut not in ('EN_PREPARATION', 'INSCRIPTIONS_OUVERTES'):
            messages.error(
                request,
                "Seules les sessions en préparation ou à inscriptions ouvertes peuvent être supprimées."
            )
            return redirect('exams:detail', pk=pk)
        titre = session.titre
        # Supprimer d'abord les inscriptions et paiements liés
        PaiementExamen.objects.filter(session=session).delete()
        session.inscriptions.all().delete()
        session.affectations_jury.all().delete()
        session.delete()
        messages.success(request, f"Session « {titre} » supprimée.")
        return redirect('exams:liste')
    return render(request, 'exams/session_confirmer_action.html', {
        'session':      session,
        'titre_action': "Supprimer la session",
        'message':      f"Voulez-vous supprimer la session « {session.titre} » ? Toutes les inscriptions seront perdues.",
        'btn_class':    'btn-danger',
        'btn_label':    "Oui, supprimer définitivement",
        'url_action':   reverse('exams:supprimer', args=[pk]),
    })


@gest_ligue_requis
def valider_liste_club(request, session_pk, club_pk):
    from apps.clubs.models import Club
    session = get_object_or_404(
        SessionExamen, pk=session_pk,
        annee_sportive__ligue=request.user.ligue
    )
    club = get_object_or_404(Club, pk=club_pk, ligue=request.user.ligue)
    if request.method == 'POST':
        nb = Inscription.objects.filter(
            session=session,
            pratiquant__club=club,
            statut='PAIEMENT_VALIDE'
        ).update(statut='AUTORISE')

        if nb:
            # Générer les matricules pour les nouveaux autorisés sans matricule
            try:
                modele = request.user.ligue.modele_matricule
                annee  = session.annee_sportive.date_debut.year
                nouveaux = (
                    Inscription.objects
                    .filter(session=session, pratiquant__club=club, statut='AUTORISE',
                            pratiquant__matricule__isnull=True)
                    .select_related('pratiquant')
                )
                with transaction.atomic():
                    locked = ModeleMatricule.objects.select_for_update().get(pk=modele.pk)
                    for insc in nouveaux:
                        if not insc.pratiquant.matricule:
                            insc.pratiquant.matricule = locked.generer(annee)
                            insc.pratiquant.save(update_fields=['matricule'])
            except ModeleMatricule.DoesNotExist:
                pass

            messages.success(
                request,
                f"Liste de « {club.nom_club} » validée : {nb} pratiquant(s) autorisé(s)."
            )
        else:
            messages.warning(request, "Aucune inscription en attente de validation pour ce club.")
    return redirect('exams:detail', pk=session_pk)


@gest_club_requis
def sessions_ouvertes(request):
    club     = request.user.club
    sessions = (
        SessionExamen.objects
        .filter(annee_sportive__ligue=club.ligue, statut='INSCRIPTIONS_OUVERTES')
        .select_related('annee_sportive')
        .order_by('date_examen')
    )
    return render(request, 'exams/club_sessions.html', {
        'sessions': sessions,
        'club':     club,
    })


@gest_club_requis
def session_inscriptions_club(request, session_pk):
    from apps.payments.models import PaiementExamen
    club    = request.user.club
    session = get_object_or_404(
        SessionExamen, pk=session_pk,
        annee_sportive__ligue=club.ligue,
    )
    inscriptions = (
        session.inscriptions
        .filter(pratiquant__club=club)
        .select_related('pratiquant', 'grade_vise', 'option')
        .order_by('pratiquant__nom', 'pratiquant__prenom')
    )
    montant_total = inscriptions.aggregate(total=Sum('montant'))['total'] or 0
    paiement = PaiementExamen.objects.filter(club=club, session=session).first()
    return render(request, 'exams/club_session_inscriptions.html', {
        'session':       session,
        'club':          club,
        'inscriptions':  inscriptions,
        'montant_total': montant_total,
        'paiement':      paiement,
        'peut_inscrire': session.statut == 'INSCRIPTIONS_OUVERTES',
        'peut_payer':    session.statut in ['INSCRIPTIONS_OUVERTES', 'INSCRIPTIONS_CLOSES', 'EN_COURS'],
    })


@gest_club_requis
def inscrire_pratiquant(request, session_pk):
    import json
    club    = request.user.club
    session = get_object_or_404(
        SessionExamen, pk=session_pk,
        annee_sportive__ligue=club.ligue,
        statut='INSCRIPTIONS_OUVERTES',
    )
    ligue  = club.ligue
    form   = MultiInscriptionForm(club=club, session=session, ligue=ligue)

    if request.method == 'POST':
        form = MultiInscriptionForm(request.POST, club=club, session=session, ligue=ligue)
        if form.is_valid():
            grade_vise  = form.cleaned_data['grade_vise']
            option      = form.cleaned_data.get('option')
            pratiquants = form.cleaned_data['pratiquants']
            nb_ok = 0
            for p in pratiquants:
                if not Inscription.objects.filter(session=session, pratiquant=p).exists():
                    Inscription.objects.create(
                        session=session, pratiquant=p,
                        grade_vise=grade_vise, option=option,
                    )
                    nb_ok += 1
            if nb_ok:
                messages.success(request, f"{nb_ok} pratiquant(s) inscrit(s) pour le grade « {grade_vise} ».")
            return redirect('exams:club_inscriptions', session_pk=session_pk)
        else:
            for errs in form.errors.values():
                for e in errs:
                    messages.error(request, e)

    # Préparer les pratiquants disponibles avec leurs données pour le JS
    deja_inscrits = Inscription.objects.filter(session=session).values_list('pratiquant_id', flat=True)
    pratiquants_dispo = (
        club.pratiquants.filter(actif=True)
        .exclude(pk__in=deja_inscrits)
        .select_related('grade_actuel')
        .order_by('nom', 'prenom')
    )
    # Sérialiser pour le filtre JS
    pratiquants_json = json.dumps([
        {
            'pk':          p.pk,
            'nom':         f"{p.nom} {p.prenom}",
            'grade_nom':   p.grade_actuel.nom if p.grade_actuel else "Sans grade",
            'grade_ordre': p.grade_actuel.ordre if p.grade_actuel else -1,
        }
        for p in pratiquants_dispo
    ])
    grades = Grade.objects.filter(ligue=ligue, actif=True).order_by('ordre')
    options = OptionExamen.objects.filter(ligue=ligue, actif=True)

    return render(request, 'exams/inscrire_pratiquants.html', {
        'session':          session,
        'club':             club,
        'form':             form,
        'pratiquants_dispo': pratiquants_dispo,
        'pratiquants_json': pratiquants_json,
        'grades':           grades,
        'options':          options,
        'nb_dispo':         pratiquants_dispo.count(),
    })


@gest_club_requis
def supprimer_inscription(request, pk):
    club        = request.user.club
    inscription = get_object_or_404(Inscription, pk=pk, pratiquant__club=club)
    session_pk  = inscription.session.pk
    if request.method == 'POST':
        if inscription.statut != 'EN_ATTENTE_PAIEMENT':
            messages.error(request, "Impossible de supprimer une inscription dont le paiement est déjà validé.")
        else:
            nom = f"{inscription.pratiquant.prenom} {inscription.pratiquant.nom}"
            inscription.delete()
            messages.success(request, f"Inscription de {nom} supprimée.")
    return redirect('exams:club_inscriptions', session_pk=session_pk)
