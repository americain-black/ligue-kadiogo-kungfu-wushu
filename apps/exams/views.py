import csv
# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect, get_object_or_404
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [missing-import]
from django.contrib import messages
# pyrefly: ignore [missing-import]
from django.core.exceptions import ValidationError
# pyrefly: ignore [missing-import]
from django.http import HttpResponse
# pyrefly: ignore [missing-import]
from django.urls import reverse
# pyrefly: ignore [missing-import]
from django.db.models import Sum, Count, Q

# pyrefly: ignore [missing-import]
from django.db import transaction
from .models import SessionExamen, AffectationJury, Inscription, AnneeSportive, TarifExamen, Rubrique, RubriqueGrade, OptionExamen, ModeleMatricule, ParametresExamen
from .forms import SessionExamenForm, MultiInscriptionForm, AffectationJuryForm, AnneeSportiveForm, TarifExamenForm, RubriqueForm, RubriqueGradeForm, OptionExamenForm, ModeleMatriculeForm, ParametresExamenForm
from apps.payments.models import PaiementExamen
from apps.practitioners.models import Grade


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
def tarifs_accueil(request):
    """Redirige vers les tarifs de l'année sportive active (ou la plus récente)."""
    ligue = request.user.ligue
    annee = (
        AnneeSportive.objects.filter(ligue=ligue, statut='ACTIVE').first()
        or AnneeSportive.objects.filter(ligue=ligue).first()
    )
    if annee:
        return redirect('exams:tarifs', annee_pk=annee.pk)
    messages.info(request, "Créez d'abord une année sportive pour définir des tarifs.")
    return redirect('exams:annees_sportives')


@gest_ligue_requis
def liste_tarifs(request, annee_pk):
    annee = get_object_or_404(AnneeSportive, pk=annee_pk, ligue=request.user.ligue)
    ligue = request.user.ligue
    tarifs = annee.tarifs.select_related('grade').order_by('grade__id_grade')

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
        'tarifs':       annee.tarifs.select_related('grade').order_by('grade__id_grade'),
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
    assocs   = rubrique.rubrique_grades.select_related('grade').order_by('grade__id_grade')

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

    assocs = rubrique.rubrique_grades.select_related('grade').order_by('grade__id_grade')
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
def gerer_parametres_examen(request):
    ligue   = request.user.ligue
    params  = ParametresExamen.objects.filter(ligue=ligue).first()

    if request.method == 'POST':
        form = ParametresExamenForm(request.POST, instance=params)
        if form.is_valid():
            p = form.save(commit=False)
            p.ligue = ligue
            p.save()
            messages.success(
                request,
                f"Paramètres enregistrés : le GC reverse {p.pourcentage_ligue} % "
                f"des droits d'examen à la ligue (garde {p.pourcentage_club} %)."
            )
            return redirect('exams:parametres_examen')
    else:
        form = ParametresExamenForm(instance=params)

    return render(request, 'exams/parametres_examen.html', {
        'params': params,
        'form':   form,
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
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    return render(request, 'exams/session_detail.html', {
        'session':     session,
        'nb_inscrits': session.inscriptions.count(),
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
        'message':      f"Voulez-vous clôturer les inscriptions pour « {session.titre} » ? Les clubs ne pourront plus inscrire de licenciés.",
        'btn_class':    'btn-warning',
        'btn_label':    "Oui, clôturer les inscriptions",
        'url_action':   reverse('exams:cloturer_inscriptions', args=[pk]),
    })


@gest_ligue_requis
def gestion_session(request, pk):
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    statuts_cycle = [
        ('EN_PREPARATION',        'Préparation',           1),
        ('INSCRIPTIONS_OUVERTES', 'Inscriptions ouvertes', 2),
        ('INSCRIPTIONS_CLOSES',   'Inscriptions closes',   3),
        ('EN_COURS',              'Examen en cours',       4),
        ('CLOTUREE',              'Session clôturée',      5),
        ('RESULTATS_PUBLIES',     'Résultats publiés',     6),
    ]
    nb_inscrits = session.inscriptions.count()
    return render(request, 'exams/gestion_session.html', {
        'session':       session,
        'statuts_cycle': statuts_cycle,
        'nb_inscrits':   nb_inscrits,
    })


@gest_ligue_requis
def traiter_dossiers(request, pk):
    """Vue niveau 1 : liste des clubs avec résumé paiement."""
    from apps.payments.models import PaiementExamen
    from apps.clubs.models import Club
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    params = ParametresExamen.objects.filter(ligue=request.user.ligue).first()
    pourcentage_ligue = params.pourcentage_ligue if params else 100

    inscriptions = (
        session.inscriptions
        .select_related('pratiquant__club', 'grade_vise')
        .order_by('pratiquant__club__nom_club')
    )
    clubs_dict = {}
    for insc in inscriptions:
        club = insc.pratiquant.club
        if club.pk not in clubs_dict:
            clubs_dict[club.pk] = {
                'club': club, 'nb_inscrits': 0, 'montant_total': 0, 'paiement': None,
                'nb_autorises': 0, 'nb_exclus': 0,
            }
        clubs_dict[club.pk]['nb_inscrits'] += 1
        clubs_dict[club.pk]['montant_total'] += insc.montant or 0
        if insc.statut == 'AUTORISE':
            clubs_dict[club.pk]['nb_autorises'] += 1
        if insc.statut == 'EXCLU':
            clubs_dict[club.pk]['nb_exclus'] += 1

    paiements = (
        PaiementExamen.objects.filter(session=session)
        .select_related('club').order_by('club_id', '-date_soumission')
    )
    paiements_par_club = {}
    for p in paiements:
        if p.club_id not in paiements_par_club:
            paiements_par_club[p.club_id] = p
        elif paiements_par_club[p.club_id].statut == 'VALIDE' and p.statut in ('EN_ATTENTE', 'INSUFFISANT', 'REJETE'):
            paiements_par_club[p.club_id] = p

    for club_pk, data in clubs_dict.items():
        data['paiement'] = paiements_par_club.get(club_pk)
        mt = data['montant_total']
        data['part_ligue'] = round(mt * pourcentage_ligue / 100)
        data['part_club']  = round(mt - data['part_ligue'])

    clubs_list = list(clubs_dict.values())
    total_pratiquants  = sum(d['nb_inscrits']  for d in clubs_list)
    total_autorises    = sum(d['nb_autorises'] for d in clubs_list)
    total_exclus       = sum(d['nb_exclus']    for d in clubs_list)
    nb_paie_valides    = sum(1 for d in clubs_list if d['paiement'] and d['paiement'].statut == 'VALIDE')
    nb_paie_en_attente = len(clubs_list) - nb_paie_valides

    return render(request, 'exams/traiter_dossiers.html', {
        'session':             session,
        'clubs_data':          clubs_list,
        'params':              params,
        'total_pratiquants':   total_pratiquants,
        'total_autorises':     total_autorises,
        'total_exclus':        total_exclus,
        'nb_paie_valides':     nb_paie_valides,
        'nb_paie_en_attente':  nb_paie_en_attente,
    })


@gest_ligue_requis
def traiter_dossier_club(request, session_pk, club_pk):
    """Vue niveau 2 : dossier complet d'un club."""
    from apps.payments.models import PaiementExamen
    from apps.clubs.models import Club
    session = get_object_or_404(
        SessionExamen, pk=session_pk,
        annee_sportive__ligue=request.user.ligue
    )
    club = get_object_or_404(Club, pk=club_pk, ligue=request.user.ligue)
    params = ParametresExamen.objects.filter(ligue=request.user.ligue).first()
    pourcentage_ligue = params.pourcentage_ligue if params else 100

    inscriptions = (
        session.inscriptions
        .filter(pratiquant__club=club)
        .select_related('pratiquant', 'pratiquant__grade_actuel', 'grade_vise', 'option')
        .order_by('pratiquant__nom', 'pratiquant__prenom')
    )
    inscriptions = list(inscriptions)
    montant_total    = sum(i.montant or 0 for i in inscriptions)
    part_ligue       = round(montant_total * pourcentage_ligue / 100)
    part_club        = round(montant_total - part_ligue)
    pourcentage_club = 100 - pourcentage_ligue
    nb_inscrits      = len(inscriptions)
    nb_autorises     = sum(1 for i in inscriptions if i.statut == 'AUTORISE')
    nb_exclus        = sum(1 for i in inscriptions if i.statut == 'EXCLU')

    paiement = (
        PaiementExamen.objects.filter(club=club, session=session)
        .order_by('-date_soumission').first()
    )
    # Paiement actif : préférer le dernier non-VALIDE, sinon le dernier validé
    paiement_actif = (
        PaiementExamen.objects.filter(club=club, session=session)
        .exclude(statut='VALIDE').order_by('-date_soumission').first()
    ) or paiement

    historique_paiements = list(
        PaiementExamen.objects.filter(club=club, session=session)
        .order_by('-date_soumission')
    )
    a_paiement_valide_en_attente = any(
        i.statut == 'PAIEMENT_VALIDE' for i in inscriptions
    )

    return render(request, 'exams/traiter_dossier_club.html', {
        'session':                      session,
        'club':                         club,
        'inscriptions':                 inscriptions,
        'nb_inscrits':                  nb_inscrits,
        'nb_autorises':                 nb_autorises,
        'nb_exclus':                    nb_exclus,
        'montant_total':                montant_total,
        'part_ligue':                   part_ligue,
        'part_club':                    part_club,
        'pourcentage_ligue':            pourcentage_ligue,
        'pourcentage_club':             pourcentage_club,
        'paiement':                     paiement_actif,
        'historique_paiements':         historique_paiements,
        'a_paiement_valide_en_attente': a_paiement_valide_en_attente,
        'params':                       params,
    })


@gest_ligue_requis
def cloturer_session(request, pk):
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    if request.method == 'POST':
        try:
            session.cloturer_session()
            messages.success(request, "Session clôturée.")
        except ValidationError as e:
            messages.error(request, e.message)
        return redirect('exams:detail', pk=pk)
    return render(request, 'exams/session_confirmer_action.html', {
        'session':      session,
        'titre_action': "Clôturer la session",
        'message':      f"Voulez-vous clôturer la session « {session.titre} » ? L'examen est terminé.",
        'btn_class':    'btn-danger',
        'btn_label':    "Oui, clôturer la session",
        'url_action':   reverse('exams:cloturer_session', args=[pk]),
    })


@gest_ligue_requis
def publier_resultats(request, pk):
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    if request.method == 'POST':
        try:
            session.publier_resultats()
            messages.success(request, "Résultats publiés.")
        except ValidationError as e:
            messages.error(request, e.message)
        return redirect('exams:detail', pk=pk)
    return render(request, 'exams/session_confirmer_action.html', {
        'session':      session,
        'titre_action': "Publier les résultats",
        'message':      f"Voulez-vous publier les résultats de « {session.titre} » ? Cette action est définitive.",
        'btn_class':    'btn-info',
        'btn_label':    "Oui, publier les résultats",
        'url_action':   reverse('exams:publier_resultats', args=[pk]),
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


@gest_ligue_requis
def gestion_jury(request, pk):
    import json
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    ligue = request.user.ligue
    if request.method == 'POST':
        form = AffectationJuryForm(request.POST, session=session, ligue=ligue)
        if form.is_valid():
            aff = form.save(commit=False)
            aff.session = session
            aff.save()
            messages.success(request, f"{aff.jury} ajouté au jury.")
        else:
            messages.error(request, "Impossible d'ajouter ce membre du jury.")
        return redirect('exams:gestion_jury', pk=pk)

    jury_form    = AffectationJuryForm(session=session, ligue=ligue)
    affectations = (
        session.affectations_jury
        .select_related('jury')
        .prefetch_related('grades', 'options', 'rubriques')
        .order_by('date_affectation')
    )
    return render(request, 'exams/gestion_jury.html', {
        'session':      session,
        'jury_form':    jury_form,
        'affectations': affectations,
    })


@gest_ligue_requis
def configurer_jury(request, session_pk, affectation_pk):
    import json
    session     = get_object_or_404(
        SessionExamen, pk=session_pk,
        annee_sportive__ligue=request.user.ligue
    )
    affectation = get_object_or_404(AffectationJury, pk=affectation_pk, session=session)
    ligue       = request.user.ligue

    from apps.practitioners.models import Grade as GradeModel
    grades  = GradeModel.objects.filter(ligue=ligue).order_by('id_grade')
    options = OptionExamen.objects.filter(ligue=ligue, actif=True).order_by('nom')

    rubrique_grades = (
        RubriqueGrade.objects
        .filter(grade__ligue=ligue, actif=True)
        .select_related('rubrique', 'grade')
        .order_by('grade__id_grade', 'rubrique__nom')
    )
    rubriques_par_grade = {}
    for rg in rubrique_grades:
        gid = str(rg.grade_id)
        rubriques_par_grade.setdefault(gid, []).append({
            'pk': rg.rubrique_id, 'nom': rg.rubrique.nom
        })

    if request.method == 'POST':
        grade_ids    = request.POST.getlist('grades')
        option_ids   = request.POST.getlist('options')
        rubrique_ids = request.POST.getlist('rubriques')
        affectation.grades.set(GradeModel.objects.filter(pk__in=grade_ids))
        affectation.options.set(OptionExamen.objects.filter(pk__in=option_ids))
        affectation.rubriques.set(Rubrique.objects.filter(pk__in=rubrique_ids))
        messages.success(request, f"Configuration de {affectation.jury} enregistrée.")
        return redirect('exams:gestion_jury', pk=session_pk)

    # Rubriques déjà prises par les AUTRES jury de cette session
    rubriques_prises = set(
        AffectationJury.objects
        .filter(session=session)
        .exclude(pk=affectation.pk)
        .values_list('rubriques__pk', flat=True)
    ) - {None}

    return render(request, 'exams/configurer_jury.html', {
        'session':             session,
        'affectation':         affectation,
        'grades':              grades,
        'options':             options,
        'rubriques_par_grade': json.dumps(rubriques_par_grade),
        'grades_affectes':     set(affectation.grades.values_list('pk', flat=True)),
        'options_affectees':   set(affectation.options.values_list('pk', flat=True)),
        'rubriques_affectees': set(affectation.rubriques.values_list('pk', flat=True)),
        'rubriques_prises':    json.dumps(list(rubriques_prises)),
    })


@gest_ligue_requis
def exclure_inscription(request, pk):
    from decimal import Decimal
    insc = get_object_or_404(
        Inscription, pk=pk,
        session__annee_sportive__ligue=request.user.ligue
    )
    if request.method == 'POST':
        if insc.statut in ('EN_ATTENTE_PAIEMENT', 'PAIEMENT_VALIDE'):
            insc.statut          = 'EXCLU'
            insc.motif_exclusion = request.POST.get('motif_exclusion', '').strip()
            insc.save(update_fields=['statut', 'motif_exclusion'])
            messages.success(request, f"{insc.pratiquant} exclu(e) de la session.")

            # Vérifier si un paiement INSUFFISANT devient suffisant après l'exclusion
            paiement = PaiementExamen.objects.filter(
                club=insc.pratiquant.club,
                session=insc.session,
                statut='INSUFFISANT',
            ).first()
            if paiement:
                ligue = insc.session.annee_sportive.ligue
                params = ParametresExamen.objects.filter(ligue=ligue).first()
                pourcentage = params.pourcentage_ligue if params else Decimal('100')

                montant_brut = Inscription.objects.filter(
                    session=insc.session,
                    pratiquant__club=insc.pratiquant.club,
                    statut='EN_ATTENTE_PAIEMENT',
                ).aggregate(total=Sum('montant'))['total'] or Decimal('0')

                nouveau_attendu = (montant_brut * pourcentage / Decimal('100')).quantize(Decimal('1'))

                if paiement.montant_paye >= nouveau_attendu:
                    # pyrefly: ignore [missing-import]
                    from django.utils import timezone
                    from apps.payments.models import HistoriquePaiementExamen
                    paiement.montant_attendu = nouveau_attendu
                    paiement.statut          = 'VALIDE'
                    paiement.valide_par      = request.user
                    paiement.date_validation = timezone.now()
                    paiement.save(update_fields=['montant_attendu', 'statut', 'valide_par', 'date_validation'])
                    Inscription.objects.filter(
                        session=insc.session,
                        pratiquant__club=insc.pratiquant.club,
                        statut='EN_ATTENTE_PAIEMENT',
                    ).update(statut='PAIEMENT_VALIDE')
                    HistoriquePaiementExamen.objects.create(
                        paiement    = paiement,
                        action      = 'VALIDE',
                        acteur      = request.user,
                        montant     = paiement.montant_paye,
                        motif       = (
                            f"Validation automatique suite à l'exclusion de "
                            f"{insc.pratiquant.nom} {insc.pratiquant.prenom} "
                            f"par le gestionnaire de ligue. "
                            f"Nouveau montant dû : {nouveau_attendu} FCFA — "
                            f"Montant payé : {paiement.montant_paye} FCFA."
                        ),
                    )
                    messages.success(
                        request,
                        f"Paiement de « {insc.pratiquant.club} » régularisé automatiquement "
                        f"({paiement.montant_paye} FCFA ≥ {nouveau_attendu} FCFA requis) — Validé."
                    )
                else:
                    paiement.montant_attendu = nouveau_attendu
                    paiement.save(update_fields=['montant_attendu'])
        else:
            messages.error(request, "Ce candidat ne peut pas être exclu dans son état actuel.")
    return redirect('exams:traiter_dossier_club', session_pk=insc.session.pk, club_pk=insc.pratiquant.club.pk)


@gest_ligue_requis
def reintegrer_inscription(request, pk):
    from decimal import Decimal
    insc = get_object_or_404(
        Inscription, pk=pk,
        session__annee_sportive__ligue=request.user.ligue
    )
    if request.method == 'POST':
        if insc.statut == 'EXCLU':
            insc.statut          = 'EN_ATTENTE_PAIEMENT'
            insc.motif_exclusion = ''
            insc.save(update_fields=['statut', 'motif_exclusion'])
            messages.success(
                request,
                f"{insc.pratiquant.nom} {insc.pratiquant.prenom} réintégré(e) — "
                f"en attente de paiement."
            )

            ligue      = insc.session.annee_sportive.ligue
            params     = ParametresExamen.objects.filter(ligue=ligue).first()
            pourcentage = params.pourcentage_ligue if params else Decimal('100')

            montant_brut = Inscription.objects.filter(
                session=insc.session,
                pratiquant__club=insc.pratiquant.club,
                statut='EN_ATTENTE_PAIEMENT',
            ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
            nouveau_attendu = (montant_brut * pourcentage / Decimal('100')).quantize(Decimal('1'))

            # Si paiement INSUFFISANT : mettre à jour le montant attendu
            paiement_insuf = PaiementExamen.objects.filter(
                club=insc.pratiquant.club,
                session=insc.session,
                statut='INSUFFISANT',
            ).first()
            if paiement_insuf:
                paiement_insuf.montant_attendu = nouveau_attendu
                paiement_insuf.save(update_fields=['montant_attendu'])

            # Si paiement VALIDE (auto-validé avant) : noter dans l'historique
            # que le pratiquant réintégré nécessite un complément
            paiement_valide = PaiementExamen.objects.filter(
                club=insc.pratiquant.club,
                session=insc.session,
                statut='VALIDE',
            ).first()
            if paiement_valide:
                from apps.payments.models import HistoriquePaiementExamen
                HistoriquePaiementExamen.objects.create(
                    paiement = paiement_valide,
                    action   = 'RESOUMIS',
                    acteur   = request.user,
                    montant  = insc.montant,
                    motif    = (
                        f"Réintégration de {insc.pratiquant.nom} {insc.pratiquant.prenom} "
                        f"par le GL. Un complément de {nouveau_attendu} FCFA est attendu du club."
                    ),
                )
                messages.warning(
                    request,
                    f"Le paiement précédemment validé ne couvre pas ce licencié. "
                    f"Veuillez régulariser le paiement."
                )
        else:
            messages.error(request, "Ce licencié n'est pas exclu.")
    return redirect('exams:traiter_dossier_club', session_pk=insc.session.pk, club_pk=insc.pratiquant.club.pk)


# ── Vues GEST_CLUB — Inscriptions ─────────────────────────────────────────────

@gest_ligue_requis
def supprimer_session(request, pk):
    from apps.payments.models import PaiementExamen
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    if request.method == 'POST':
        titre = session.titre
        PaiementExamen.objects.filter(session=session).delete()
        session.inscriptions.all().delete()
        session.affectations_jury.all().delete()
        session.delete()
        messages.success(request, f"Session « {titre} » supprimée.")
        return redirect('exams:liste')
    nb_inscrits = session.inscriptions.count()
    if nb_inscrits:
        message = (
            f"Voulez-vous supprimer la session « {session.titre} » ?\n"
            f"Cette action supprimera définitivement {nb_inscrits} inscription(s) "
            f"ainsi que tous les paiements et affectations de jury associés."
        )
    else:
        message = f"Voulez-vous supprimer la session « {session.titre} » ? Cette action est irréversible."
    return render(request, 'exams/session_confirmer_action.html', {
        'session':      session,
        'titre_action': "Supprimer la session",
        'message':      message,
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
            nb_matricules = 0
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
                            nb_matricules += 1
            except (ModeleMatricule.DoesNotExist, AttributeError):
                messages.warning(
                    request,
                    "Aucun modèle de matricule configuré pour cette ligue. "
                    "Les licenciés autorisés n'ont pas encore reçu de matricule. "
                    "Définissez d'abord un modèle de matricule dans les paramètres de la ligue."
                )

            msg = f"Liste de « {club.nom_club} » validée : {nb} licencié(s) autorisé(s)."
            if nb_matricules:
                msg += f" {nb_matricules} matricule(s) attribué(s) automatiquement."
            messages.success(request, msg)
        else:
            messages.warning(request, "Aucune inscription en attente de validation pour ce club.")
    return redirect('exams:detail', pk=session_pk)


@gest_club_requis
def sessions_ouvertes(request):
    club = request.user.club
    qs = (
        SessionExamen.objects
        .filter(annee_sportive__ligue=club.ligue)
        .select_related('annee_sportive')
        .annotate(
            nb_licencies=Count(
                'inscriptions',
                filter=Q(
                    inscriptions__pratiquant__club=club,
                    inscriptions__statut__in=['PAIEMENT_VALIDE', 'AUTORISE']
                )
            )
        )
        .order_by('-date_examen')
    )
    TERMINEES = ('CLOTUREE', 'RESULTATS_PUBLIES')
    sessions_actives    = [s for s in qs if s.statut not in TERMINEES]
    sessions_historique = [s for s in qs if s.statut in TERMINEES]
    return render(request, 'exams/club_sessions.html', {
        'sessions_actives':    sessions_actives,
        'sessions_historique': sessions_historique,
        'club':                club,
    })


@gest_club_requis
def session_inscriptions_club(request, session_pk):
    from apps.payments.models import PaiementExamen
    from decimal import Decimal
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
    # Montant uniquement pour les inscriptions EN_ATTENTE_PAIEMENT (nouvelles, non encore couvertes)
    inscriptions_en_attente = inscriptions.filter(statut='EN_ATTENTE_PAIEMENT')
    nb_en_attente  = inscriptions_en_attente.count()
    montant_brut   = inscriptions_en_attente.aggregate(total=Sum('montant'))['total'] or Decimal('0')

    # Appliquer le pourcentage de la ligue
    params = ParametresExamen.objects.filter(ligue=club.ligue).first()
    pourcentage    = params.pourcentage_ligue if params else Decimal('100')
    montant_ligue  = (montant_brut * pourcentage / 100).quantize(Decimal('1'))

    # Paiement actif : EN_ATTENTE, INSUFFISANT ou REJETE le plus récent (pas VALIDE)
    paiement = (
        PaiementExamen.objects
        .filter(club=club, session=session)
        .exclude(statut='VALIDE')
        .order_by('-date_soumission')
        .first()
    )
    peut_payer = session.statut in ['INSCRIPTIONS_OUVERTES', 'INSCRIPTIONS_CLOSES', 'EN_COURS']
    return render(request, 'exams/club_session_inscriptions.html', {
        'session':        session,
        'club':           club,
        'inscriptions':   inscriptions,
        'nb_en_attente':  nb_en_attente,
        'montant_brut':   montant_brut,
        'montant_ligue':  montant_ligue,
        'pourcentage':    pourcentage,
        'params':         params,
        'paiement':       paiement,
        'peut_inscrire':  session.statut == 'INSCRIPTIONS_OUVERTES',
        'peut_payer':     peut_payer,
    })


@gest_club_requis
def inscrire_pratiquant(request, session_pk):
    club    = request.user.club
    session = get_object_or_404(
        SessionExamen, pk=session_pk,
        annee_sportive__ligue=club.ligue,
        statut='INSCRIPTIONS_OUVERTES',
    )
    ligue   = club.ligue
    grades  = list(Grade.objects.filter(ligue=ligue, actif=True).order_by('id_grade'))
    options = list(OptionExamen.objects.filter(ligue=ligue, actif=True))
    params  = ParametresExamen.objects.filter(ligue=ligue).first()
    pourcentage_ligue = float(params.pourcentage_ligue) if params else 100.0

    deja_inscrits = Inscription.objects.filter(session=session).values_list('pratiquant_id', flat=True)
    tous_dispos = (
        club.pratiquants.filter(actif=True)
        .exclude(pk__in=deja_inscrits)
        .select_related('grade_actuel')
        .order_by('nom', 'prenom')
    )

    # Grade visé transmis en GET (filtrage) ou en POST (inscription)
    grade_vise_pk = request.GET.get('grade_vise') or request.POST.get('grade_vise')
    grade_vise = None
    pratiquants_eligibles = []

    if grade_vise_pk:
        try:
            grade_vise = Grade.objects.get(pk=grade_vise_pk, ligue=ligue, actif=True)
            pratiquants_eligibles = [
                p for p in tous_dispos
                if p.grade_actuel and p.grade_actuel.id_grade == grade_vise.id_grade - 1
            ]
        except Grade.DoesNotExist:
            grade_vise = None

    if request.method == 'POST' and 'inscrire' in request.POST:
        if not grade_vise:
            messages.error(request, "Grade visé invalide.")
            return redirect('exams:inscrire', session_pk=session_pk)
        pks_coches = request.POST.getlist('pratiquants')
        if not pks_coches:
            messages.error(request, "Aucun licencié sélectionné.")
        else:
            nb_ok = 0
            bulletins_manquants = []
            options_manquantes = []
            for p in pratiquants_eligibles:
                if str(p.pk) not in pks_coches:
                    continue
                bulletin = request.FILES.get(f'bulletin_{p.pk}')
                if p.grade_actuel and p.grade_actuel.id_grade >= 2 and not bulletin and not p.bulletin_grade:
                    bulletins_manquants.append(f"{p.nom} {p.prenom}")
                    continue
                option = None
                option_pk = request.POST.get(f'option_{p.pk}')
                if options and not option_pk:
                    options_manquantes.append(f"{p.nom} {p.prenom}")
                    continue
                if option_pk:
                    try:
                        option = OptionExamen.objects.get(pk=option_pk)
                    except OptionExamen.DoesNotExist:
                        pass
                if not Inscription.objects.filter(session=session, pratiquant=p).exists():
                    insc = Inscription(session=session, pratiquant=p, grade_vise=grade_vise, option=option)
                    if bulletin:
                        insc.bulletin = bulletin
                    insc.save()
                    nb_ok += 1
            if bulletins_manquants:
                messages.error(
                    request,
                    "Bulletin manquant pour : " + ", ".join(bulletins_manquants)
                    + " — ces pratiquants n'ont pas été inscrits."
                )
            if options_manquantes:
                messages.error(
                    request,
                    "Option non choisie pour : " + ", ".join(options_manquantes)
                    + " — ces pratiquants n'ont pas été inscrits."
                )
            if nb_ok:
                messages.success(request, f"{nb_ok} pratiquant(s) inscrit(s) pour le grade « {grade_vise} ».")
            return redirect('exams:club_inscriptions', session_pk=session_pk)

    tarif_grade_vise = None
    if grade_vise and params:
        tarif_obj = TarifExamen.objects.filter(
            annee_sportive=session.annee_sportive, grade=grade_vise
        ).first()
        tarif_grade_vise = tarif_obj.montant if tarif_obj else None

    return render(request, 'exams/inscrire_pratiquants.html', {
        'session':               session,
        'club':                  club,
        'grades':                grades,
        'options':               options,
        'grade_vise':            grade_vise,
        'pratiquants_eligibles': pratiquants_eligibles,
        'nb_total_dispo':        tous_dispos.count(),
        'tarif_grade_vise':      tarif_grade_vise,
        'pourcentage_ligue':     pourcentage_ligue,
        'params':                params,
    })


@gest_club_requis
def supprimer_inscription(request, pk):
    from decimal import Decimal
    from apps.payments.models import PaiementExamen
    club        = request.user.club
    inscription = get_object_or_404(Inscription, pk=pk, pratiquant__club=club)
    session_pk  = inscription.session.pk
    session     = inscription.session
    if request.method == 'POST':
        if inscription.statut != 'EN_ATTENTE_PAIEMENT':
            messages.error(request, "Impossible de supprimer une inscription dont le paiement est déjà validé.")
        else:
            nom = f"{inscription.pratiquant.prenom} {inscription.pratiquant.nom}"
            inscription.delete()
            messages.success(request, f"Inscription de {nom} supprimée.")
            # Recalcul automatique si un paiement INSUFFISANT existe
            paiement_insuffisant = (
                PaiementExamen.objects
                .filter(club=club, session=session, statut='INSUFFISANT')
                .order_by('-date_soumission')
                .first()
            )
            if paiement_insuffisant:
                params = ParametresExamen.objects.filter(ligue=club.ligue).first()
                pourcentage = params.pourcentage_ligue if params else Decimal('100')
                reste = Inscription.objects.filter(
                    session=session, pratiquant__club=club, statut='EN_ATTENTE_PAIEMENT'
                ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                nouveau_attendu = (reste * pourcentage / 100).quantize(Decimal('1'))
                if paiement_insuffisant.montant_paye >= nouveau_attendu and nouveau_attendu > 0:
                    paiement_insuffisant.montant_attendu = nouveau_attendu
                    paiement_insuffisant.statut          = 'EN_ATTENTE'
                    paiement_insuffisant.motif_rejet     = ''
                    paiement_insuffisant.save()
                    messages.info(
                        request,
                        "Montant maintenant suffisant pour les inscrits restants. "
                        "Le gestionnaire financier va revalider votre dossier."
                    )
    return redirect('exams:club_inscriptions', session_pk=session_pk)


# ── Listes licenciés ─────────────────────────────────────────────────────────

STATUTS_LICENCIES = ['PAIEMENT_VALIDE', 'AUTORISE']


def _qs_licencies(session, club_pk=None, grade_pk=None):
    qs = (
        Inscription.objects
        .filter(session=session, statut__in=STATUTS_LICENCIES)
        .select_related('pratiquant__club', 'pratiquant__grade_actuel', 'grade_vise')
        .order_by('grade_vise__id_grade', 'pratiquant__nom', 'pratiquant__prenom')
    )
    if club_pk:
        qs = qs.filter(pratiquant__club_id=club_pk)
    if grade_pk:
        qs = qs.filter(grade_vise_id=grade_pk)
    return qs


def _csv_licencies(qs, filename):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['N°', 'Nom', 'Prénom', 'Sexe', 'Matricule', 'Grade actuel', 'Grade visé', 'Club'])
    for i, insc in enumerate(qs, 1):
        p = insc.pratiquant
        writer.writerow([
            i,
            p.nom,
            p.prenom,
            p.sexe,
            p.matricule or '',
            p.grade_actuel.nom if p.grade_actuel else 'Sans grade',
            insc.grade_vise.nom,
            p.club.nom_club,
        ])
    return response


@gest_ligue_requis
def liste_licencies_gl(request, pk):
    session = get_object_or_404(
        SessionExamen, pk=pk,
        annee_sportive__ligue=request.user.ligue
    )
    ligue  = request.user.ligue
    clubs  = session.inscriptions.filter(statut__in=STATUTS_LICENCIES).values_list(
        'pratiquant__club__pk', 'pratiquant__club__nom_club'
    ).distinct().order_by('pratiquant__club__nom_club')
    grades = session.inscriptions.filter(statut__in=STATUTS_LICENCIES).values_list(
        'grade_vise__pk', 'grade_vise__nom'
    ).distinct().order_by('grade_vise__id_grade')

    club_pk  = request.GET.get('club', '')
    grade_pk = request.GET.get('grade', '')
    qs = _qs_licencies(session, club_pk or None, grade_pk or None)

    if request.GET.get('format') == 'csv':
        parts = []
        if club_pk:
            parts.append(f"club{club_pk}")
        if grade_pk:
            parts.append(f"grade{grade_pk}")
        suffix = '_'.join(parts) or 'tous'
        filename = f"licencies_{session.titre.replace(' ', '_')}_{suffix}.csv"
        return _csv_licencies(qs, filename)

    return render(request, 'exams/liste_licencies_session.html', {
        'session':   session,
        'licencies': qs,
        'clubs':     clubs,
        'grades':    grades,
        'club_pk':   club_pk,
        'grade_pk':  grade_pk,
        'nb_total':  qs.count(),
    })


@gest_club_requis
def liste_licencies_club(request, session_pk):
    club    = request.user.club
    session = get_object_or_404(
        SessionExamen, pk=session_pk,
        annee_sportive__ligue=club.ligue
    )
    grades = session.inscriptions.filter(
        pratiquant__club=club, statut__in=STATUTS_LICENCIES
    ).values_list('grade_vise__pk', 'grade_vise__nom').distinct().order_by('grade_vise__id_grade')

    grade_pk = request.GET.get('grade', '')
    qs = _qs_licencies(session, club_pk=club.pk, grade_pk=grade_pk or None)

    if request.GET.get('format') == 'csv':
        suffix = f"grade{grade_pk}" if grade_pk else 'tous'
        filename = f"licencies_{club.nom_club.replace(' ', '_')}_{session.titre.replace(' ', '_')}_{suffix}.csv"
        return _csv_licencies(qs, filename)

    return render(request, 'exams/liste_licencies_club.html', {
        'session':   session,
        'club':      club,
        'licencies': qs,
        'grades':    grades,
        'grade_pk':  grade_pk,
        'nb_total':  qs.count(),
    })
