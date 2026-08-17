# pyrefly: ignore [missing-import]
import json
from django.shortcuts import render, redirect, get_object_or_404
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [missing-import]
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

from .models import Ligue, VoletOrganigramme, MembreOrganigramme
from .forms import LigueForm, VoletOrganigrammeForm, MembreOrganigrammeForm, EditerInfosLigueForm
from apps.clubs.models import Club
from apps.practitioners.models import Pratiquant, Grade
from apps.exams.models import SessionExamen, AnneeSportive, Inscription
from apps.evaluations.models import NoteRubrique
from apps.results.models import Resultat


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
    return render(request, 'ligues/formulaire.html', {'form': form, 'titre': 'Créer une Ligue'})


@super_admin_requis
def modifier_ligue(request, pk):
    ligue = get_object_or_404(Ligue, pk=pk)
    if request.method == 'POST':
        form = LigueForm(request.POST, request.FILES, instance=ligue)
        if form.is_valid():
            form.save()
            messages.success(request, "Ligue mise à jour avec succès.")
            return redirect('ligues:liste')
    else:
        form = LigueForm(instance=ligue)
    return render(request, 'ligues/formulaire.html', {'form': form, 'titre': 'Modifier la Ligue'})


@super_admin_requis
def toggle_actif_ligue(request, pk):
    ligue = get_object_or_404(Ligue, pk=pk)
    ligue.actif = not ligue.actif
    ligue.save()
    status = "activée" if ligue.actif else "désactivée"
    messages.success(request, f"Ligue « {ligue.nom_ligue} » {status}.")
    return redirect('ligues:liste')


def organigramme(request):
    if request.user.is_authenticated and getattr(request.user, 'ligue', None):
        ligue = request.user.ligue
    else:
        ligue = Ligue.objects.filter(sigle='LKKFW').first() or Ligue.objects.first()

    if not ligue:
        messages.error(request, "Aucune ligue trouvée.")
        return redirect('accounts:accueil')

    volets = ligue.volets.prefetch_related('membres__club').all()
    form_volet  = VoletOrganigrammeForm()
    form_membre = MembreOrganigrammeForm()
    peut_modifier = request.user.is_authenticated and (request.user.is_superuser or request.user.est_gest_ligue())

    return render(request, 'ligues/organigramme.html', {
        'ligue':         ligue,
        'volets':        volets,
        'form_volet':    form_volet,
        'form_membre':   form_membre,
        'peut_modifier': peut_modifier,
    })


def organigramme_visuel(request):
    if request.user.is_authenticated and getattr(request.user, 'ligue', None):
        ligue = request.user.ligue
    else:
        ligue = Ligue.objects.filter(sigle='LKKFW').first() or Ligue.objects.first()

    if not ligue:
        messages.error(request, "Aucune ligue trouvée.")
        return redirect('accounts:accueil')

    volets = ligue.volets.prefetch_related('membres__club').all()
    for volet in volets:
        membres = list(volet.membres.filter(actif=True, club__isnull=True).order_by('ordre', 'nom'))
        niveaux_dict = {}
        for m in membres:
            niveaux_dict.setdefault(m.ordre, []).append(m)
        
        volet.niveaux_membres = [
            {'niveau': lvl, 'membres': sorted(m_list, key=lambda x: x.nom)}
            for lvl, m_list in sorted(niveaux_dict.items())
        ]
    return render(request, 'ligues/organigramme_visuel.html', {
        'ligue':  ligue,
        'volets': volets,
    })


@gest_ligue_requis
def ajouter_volet(request):
    if request.method == 'POST':
        form = VoletOrganigrammeForm(request.POST)
        if form.is_valid():
            volet = form.save(commit=False)
            volet.ligue = request.user.ligue
            volet.save()
            messages.success(request, f"Volet « {volet.nom_volet} » créé avec succès.")
    return redirect('ligues:organigramme')


@gest_ligue_requis
def supprimer_volet(request, pk):
    volet = get_object_or_404(VoletOrganigramme, pk=pk, ligue=request.user.ligue)
    if request.method == 'POST':
        nom = volet.nom_volet
        volet.delete()
        messages.success(request, f"Volet « {nom} » et tous ses membres ont été supprimés.")
    return redirect('ligues:organigramme')


@gest_ligue_requis
def ajouter_membre(request, volet_pk):
    volet = get_object_or_404(VoletOrganigramme, pk=volet_pk, ligue=request.user.ligue)
    if request.method == 'POST':
        form = MembreOrganigrammeForm(request.POST)
        if form.is_valid():
            membre = form.save(commit=False)
            membre.volet = volet
            membre.save()
            messages.success(request, f"{membre.prenom} {membre.nom} ajouté au volet « {volet.nom_volet} ».")
    return redirect('ligues:organigramme')


@gest_ligue_requis
def modifier_membre(request, pk):
    membre = get_object_or_404(MembreOrganigramme, pk=pk, volet__ligue=request.user.ligue)
    if request.method == 'POST':
        form = MembreOrganigrammeForm(request.POST, instance=membre)
        if form.is_valid():
            form.save()
            messages.success(request, f"Membre « {membre.prenom} {membre.nom} » mis à jour.")
            return redirect('ligues:organigramme')
    else:
        form = MembreOrganigrammeForm(instance=membre)

    return render(request, 'ligues/form_membre.html', {
        'form': form,
        'membre': membre,
    })


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


@gest_ligue_requis
def reporting_dashboard(request):
    """
    Tableau de bord décisionnel & Reporting de la Ligue.
    Calculs dynamiques en temps réel basés sur les modèles existants.
    """
    ligue = request.user.ligue
    if not ligue and request.user.is_superuser:
        ligue = Ligue.objects.filter(sigle='LKKFW').first() or Ligue.objects.first()

    if not ligue:
        messages.error(request, "Aucune ligue associée.")
        return redirect('accounts:tableau_de_bord')

    saisons = AnneeSportive.objects.filter(ligue=ligue).order_by('-date_debut')
    saison_id = request.GET.get('saison')
    if saison_id:
        saison_active = saisons.filter(pk=saison_id).first()
    else:
        saison_active = saisons.filter(statut='ACTIVE').first() or saisons.first()

    # 1. Filtres & Métriques de Base
    # Règle métier : Un licencié est un pratiquant qui s'est inscrit à une session d'examen et dont le dossier a été validé
    licencies_qs = Pratiquant.objects.filter(
        club__ligue=ligue,
        actif=True,
        inscriptions__statut__in=['VALIDEE', 'AUTORISE', 'PAIEMENT_VALIDE']
    ).distinct() if ligue else Pratiquant.objects.none()

    clubs_qs = Club.objects.filter(ligue=ligue, statut_club='AFFILIE') if ligue else Club.objects.none()
    sessions_qs = SessionExamen.objects.filter(annee_sportive__ligue=ligue) if ligue else SessionExamen.objects.none()
    results_qs = Resultat.objects.filter(
        inscription__session__annee_sportive__ligue=ligue,
        inscription__statut__in=['VALIDEE', 'AUTORISE', 'PAIEMENT_VALIDE']
    ) if ligue else Resultat.objects.none()

    if saison_active:
        licencies_qs = licencies_qs.filter(inscriptions__session__annee_sportive=saison_active)
        sessions_qs = sessions_qs.filter(annee_sportive=saison_active)
        results_qs = results_qs.filter(inscription__session__annee_sportive=saison_active)

    total_clubs = clubs_qs.count()
    total_pratiquants = licencies_qs.count()
    hommes_count = licencies_qs.filter(sexe='M').count()
    femmes_count = licencies_qs.filter(sexe='F').count()
    taux_parite_femmes = round((femmes_count / total_pratiquants * 100), 1) if total_pratiquants > 0 else 0

    total_sessions = sessions_qs.count()
    total_candidats = results_qs.count()
    total_admis = results_qs.filter(decision='ADMIS').count()
    total_ajournes = results_qs.filter(decision='AJOURNE').count()
    taux_reussite = round((total_admis / total_candidats * 100), 1) if total_candidats > 0 else 0
    moyenne_generale_examens = results_qs.aggregate(avg=Avg('moyenne'))['avg'] or 0.0

    # 2. Données pour Graphique : Répartition des Grades (Triés par Ordre Officiel & Couleurs Appropriées)
    def _couleur_grade(nom_grade):
        g = (nom_grade or '').upper().strip()
        if 'ROUGE' in g:
            if 'III' in g: return '#991b1b'  # Rouge foncé (ROUGE III)
            if 'II' in g:  return '#dc2626'  # Rouge vif (ROUGE II)
            if 'I' in g:   return '#ef4444'  # Rouge moyen (ROUGE I)
            return '#f87171'                 # Rouge clair (ROUGE)
        if 'JAUNE' in g:
            if 'III' in g: return '#b45309'
            if 'II' in g:  return '#d97706'
            if 'I' in g:   return '#f59e0b'
            return '#fbbf24'
        if 'BLEU' in g:    return '#2563eb'
        if 'BLANC' in g:   return '#94a3b8'
        if 'DUAN' in g or 'NOIR' in g: return '#1e293b'
        return '#64748b'

    all_grades_qs = Grade.objects.filter(Q(ligue=ligue) | Q(ligue__isnull=True), actif=True).order_by('id_grade')
    grades_counts_dict = {g.nom: 0 for g in all_grades_qs}
    grades_counts_dict['Sans grade'] = 0

    for p in pratiquants_qs.select_related('grade_actuel'):
        gn = p.grade_actuel.nom if p.grade_actuel else 'Sans grade'
        grades_counts_dict[gn] = grades_counts_dict.get(gn, 0) + 1

    grade_labels = []
    grade_data = []
    grade_colors = []

    for g_name, count in grades_counts_dict.items():
        if count > 0:
            grade_labels.append(g_name)
            grade_data.append(count)
            grade_colors.append(_couleur_grade(g_name))

    # 3. Données pour Graphique : Candidats Inscrits aux Examens par Club (Top 10)
    inscriptions_qs = Inscription.objects.filter(session__annee_sportive__ligue=ligue)
    if saison_active:
        inscriptions_qs = inscriptions_qs.filter(session__annee_sportive=saison_active)

    clubs_inscrits = list(
        inscriptions_qs.values('pratiquant__club__nom_club')
        .annotate(nb_inscrits=Count('id'))
        .order_by('-nb_inscrits')[:10]
    )
    club_labels = [c['pratiquant__club__nom_club'] for c in clubs_inscrits if c['pratiquant__club__nom_club']]
    club_data = [c['nb_inscrits'] for c in clubs_inscrits if c['pratiquant__club__nom_club']]

    # 4. Données pour Graphique : Performance par Rubrique d'Examen
    notes_qs = NoteRubrique.objects.filter(
        inscription__session__annee_sportive__ligue=ligue
    )
    if saison_active:
        notes_qs = notes_qs.filter(inscription__session__annee_sportive=saison_active)

    rubriques_stats = list(
        notes_qs.values('rubrique_grade__rubrique__nom')
        .annotate(moyenne_rubrique=Avg('note'))
        .order_by('-moyenne_rubrique')
    )
    rubrique_labels = [r['rubrique_grade__rubrique__nom'] for r in rubriques_stats]
    rubrique_data = [round(float(r['moyenne_rubrique']), 2) for r in rubriques_stats]

    # 5. Données par Session d'Examen
    sessions_stats = []
    for s in sessions_qs.order_by('date_examen'):
        res_s = Resultat.objects.filter(inscription__session=s)
        cnt = res_s.count()
        adm = res_s.filter(decision='ADMIS').count()
        moy = res_s.aggregate(avg=Avg('moyenne'))['avg'] or 0.0
        sessions_stats.append({
            'titre': s.titre,
            'date': s.date_examen,
            'candidats': cnt,
            'admis': adm,
            'taux': round((adm / cnt * 100), 1) if cnt > 0 else 0,
            'moyenne': round(float(moy), 2),
        })

    context = {
        'ligue': ligue,
        'saisons': saisons,
        'saison_active': saison_active,
        # KPIs
        'total_clubs': total_clubs,
        'total_pratiquants': total_pratiquants,
        'hommes_count': hommes_count,
        'femmes_count': femmes_count,
        'taux_parite_femmes': taux_parite_femmes,
        'total_sessions': total_sessions,
        'total_candidats': total_candidats,
        'total_admis': total_admis,
        'total_ajournes': total_ajournes,
        'taux_reussite': taux_reussite,
        'moyenne_generale_examens': round(float(moyenne_generale_examens), 2),
        'sessions_stats': sessions_stats,
        # JSON pour Chart.js
        'grade_labels_json': json.dumps(grade_labels),
        'grade_data_json': json.dumps(grade_data),
        'grade_colors_json': json.dumps(grade_colors),
        'club_labels_json': json.dumps(club_labels),
        'club_data_json': json.dumps(club_data),
        'rubrique_labels_json': json.dumps(rubrique_labels),
        'rubrique_data_json': json.dumps(rubrique_data),
        'genre_data_json': json.dumps([hommes_count, femmes_count]),
    }
    return render(request, 'ligues/reporting.html', context)


@gest_ligue_requis
def export_rapport_pdf(request):
    """
    Génération du Rapport d'Activité et Bilan Statistique Annuel en PDF avec WeasyPrint.
    """
    ligue = request.user.ligue
    if not ligue and request.user.is_superuser:
        ligue = Ligue.objects.filter(sigle='LKKFW').first() or Ligue.objects.first()

    saisons = AnneeSportive.objects.filter(ligue=ligue).order_by('-date_debut')
    saison_id = request.GET.get('saison')
    if saison_id:
        saison_active = saisons.filter(pk=saison_id).first()
    else:
        saison_active = saisons.filter(statut='ACTIVE').first() or saisons.first()

    pratiquants_qs = Pratiquant.objects.filter(club__ligue=ligue, actif=True)
    clubs_qs = Club.objects.filter(ligue=ligue, statut_club='AFFILIE')
    sessions_qs = SessionExamen.objects.filter(annee_sportive__ligue=ligue)
    results_qs = Resultat.objects.filter(inscription__session__annee_sportive__ligue=ligue)

    if saison_active:
        sessions_qs = sessions_qs.filter(annee_sportive=saison_active)
        results_qs = results_qs.filter(inscription__session__annee_sportive=saison_active)

    total_clubs = clubs_qs.count()
    total_pratiquants = pratiquants_qs.count()
    hommes_count = pratiquants_qs.filter(sexe='M').count()
    femmes_count = pratiquants_qs.filter(sexe='F').count()

    total_candidats = results_qs.count()
    total_admis = results_qs.filter(decision='ADMIS').count()
    taux_reussite = round((total_admis / total_candidats * 100), 1) if total_candidats > 0 else 0

    grades_counts = list(
        pratiquants_qs.values('grade_actuel__nom')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    inscriptions_pdf_qs = Inscription.objects.filter(session__annee_sportive__ligue=ligue)
    if saison_active:
        inscriptions_pdf_qs = inscriptions_pdf_qs.filter(session__annee_sportive=saison_active)

    clubs_counts = list(
        inscriptions_pdf_qs.values('pratiquant__club__nom_club', 'pratiquant__club__code_club')
        .annotate(nb_inscrits=Count('id'))
        .order_by('-nb_inscrits')
    )

    context = {
        'ligue': ligue,
        'saison_active': saison_active,
        'total_clubs': total_clubs,
        'total_pratiquants': total_pratiquants,
        'hommes_count': hommes_count,
        'femmes_count': femmes_count,
        'total_candidats': total_candidats,
        'total_admis': total_admis,
        'taux_reussite': taux_reussite,
        'grades_counts': grades_counts,
        'clubs_counts': clubs_counts,
        'sessions': sessions_qs,
    }

    html_string = render_to_string('ligues/rapport_activite_pdf.html', context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    saison_label = saison_active.libelle if saison_active else 'Global'
    filename = f"Rapport_Activite_{ligue.sigle}_{saison_label}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


def statistiques_publiques(request):
    """
    Portail de Statistiques Publiques de la Ligue.
    Accessible librement sans authentification pour la transparence et le rayonnement du Kung Fu Wushu.
    """
    ligue = Ligue.objects.filter(sigle='LKKFW').first() or Ligue.objects.first()

    # Récupération uniquement des saisons sportives qui possèdent des sessions d'examen
    saisons = AnneeSportive.objects.filter(ligue=ligue, sessions__isnull=False).distinct().order_by('-date_debut') if ligue else []
    saison_id = request.GET.get('saison')
    if saison_id:
        saison_active = saisons.filter(pk=saison_id).first()
    else:
        saison_active = saisons.filter(statut='ACTIVE').first() or (saisons.first() if saisons else None)

    pratiquants_qs = Pratiquant.objects.filter(club__ligue=ligue, actif=True) if ligue else Pratiquant.objects.none()
    
    # Règle métier : Un licencié est un pratiquant qui s'est inscrit à une session d'examen et dont le dossier a été validé
    licencies_qs = pratiquants_qs.filter(
        inscriptions__statut__in=['VALIDEE', 'AUTORISE', 'PAIEMENT_VALIDE']
    ).distinct()

    clubs_qs = Club.objects.filter(ligue=ligue, statut_club='AFFILIE') if ligue else Club.objects.none()
    results_qs = Resultat.objects.filter(
        inscription__session__annee_sportive__ligue=ligue,
        inscription__statut__in=['VALIDEE', 'AUTORISE', 'PAIEMENT_VALIDE'],
        publie=True
    ) if ligue else Resultat.objects.none()

    if saison_active:
        licencies_qs = licencies_qs.filter(inscriptions__session__annee_sportive=saison_active)
        results_qs = results_qs.filter(inscription__session__annee_sportive=saison_active)

    total_clubs = clubs_qs.count()
    total_pratiquants = licencies_qs.count()
    hommes_count = licencies_qs.filter(sexe='M').count()
    femmes_count = licencies_qs.filter(sexe='F').count()
    taux_parite_femmes = round((femmes_count / total_pratiquants * 100), 1) if total_pratiquants > 0 else 0

    total_candidats = results_qs.count()
    total_admis = results_qs.filter(decision='ADMIS').count()
    taux_reussite = round((total_admis / total_candidats * 100), 1) if total_candidats > 0 else 0

    # Répartition des Grades (triés par ordre officiel id_grade)
    def _couleur_grade(nom_grade):
        g = (nom_grade or '').upper().strip()
        if 'ROUGE' in g:
            if 'III' in g: return '#991b1b'
            if 'II' in g:  return '#dc2626'
            if 'I' in g:   return '#ef4444'
            return '#f87171'
        if 'JAUNE' in g:
            if 'III' in g: return '#b45309'
            if 'II' in g:  return '#d97706'
            if 'I' in g:   return '#f59e0b'
            return '#fbbf24'
        if 'BLEU' in g:    return '#2563eb'
        if 'BLANC' in g:   return '#94a3b8'
        if 'DUAN' in g or 'NOIR' in g: return '#1e293b'
        return '#64748b'

    all_grades_qs = Grade.objects.filter(Q(ligue=ligue) | Q(ligue__isnull=True), actif=True).order_by('id_grade') if ligue else []
    grades_counts_dict = {g.nom: 0 for g in all_grades_qs}
    grades_counts_dict['Sans grade'] = 0

    for p in pratiquants_qs.select_related('grade_actuel'):
        gn = p.grade_actuel.nom if p.grade_actuel else 'Sans grade'
        grades_counts_dict[gn] = grades_counts_dict.get(gn, 0) + 1

    grade_labels = []
    grade_data = []
    grade_colors = []

    for g_name, count in grades_counts_dict.items():
        if count > 0:
            grade_labels.append(g_name)
            grade_data.append(count)
            grade_colors.append(_couleur_grade(g_name))

    # Inscriptions par club
    inscriptions_qs = Inscription.objects.filter(session__annee_sportive__ligue=ligue) if ligue else Inscription.objects.none()
    if saison_active:
        inscriptions_qs = inscriptions_qs.filter(session__annee_sportive=saison_active)

    clubs_inscrits = list(
        inscriptions_qs.values('pratiquant__club__nom_club')
        .annotate(nb_inscrits=Count('id'))
        .order_by('-nb_inscrits')[:10]
    )
    club_labels = [c['pratiquant__club__nom_club'] for c in clubs_inscrits if c['pratiquant__club__nom_club']]
    club_data = [c['nb_inscrits'] for c in clubs_inscrits if c['pratiquant__club__nom_club']]

    # 5. Évolution Année par Année (Chaque Année avec sa Session 1 & Session 2 pour Hommes & Femmes)
    saisons_evolution_list = []

    for s_obj in saisons.order_by('date_debut'):
        sess_qs = SessionExamen.objects.filter(annee_sportive=s_obj).order_by('date_examen')
        sess_items = []
        for sess in sess_qs:
            inscr_sess = Inscription.objects.filter(session=sess)
            h_c = inscr_sess.filter(pratiquant__sexe='M').count()
            f_c = inscr_sess.filter(pratiquant__sexe='F').count()
            
            # Nom simplifié de la session
            titre_court = "Session 1 (Mi-Saison)" if ("Mi-Saison" in sess.titre or "Fév" in sess.titre) else "Session 2 (Fin de Saison)"
            sess_items.append({
                'id': sess.id,
                'titre': sess.titre,
                'titre_court': titre_court,
                'hommes': h_c,
                'femmes': f_c,
                'total': h_c + f_c
            })

        if sess_items:
            saisons_evolution_list.append({
                'saison': s_obj,
                'sessions': sess_items,
                'labels_json': json.dumps([s['titre_court'] for s in sess_items]),
                'hommes_json': json.dumps([s['hommes'] for s in sess_items]),
                'femmes_json': json.dumps([s['femmes'] for s in sess_items]),
            })

    context = {
        'ligue': ligue,
        'saisons': saisons,
        'saison_active': saison_active,
        'total_clubs': total_clubs,
        'total_pratiquants': total_pratiquants,
        'hommes_count': hommes_count,
        'femmes_count': femmes_count,
        'taux_parite_femmes': taux_parite_femmes,
        'total_candidats': total_candidats,
        'total_admis': total_admis,
        'taux_reussite': taux_reussite,
        'clubs': clubs_qs,
        'saisons_evolution_list': saisons_evolution_list,
        'grade_labels_json': json.dumps(grade_labels),
        'grade_data_json': json.dumps(grade_data),
        'grade_colors_json': json.dumps(grade_colors),
        'club_labels_json': json.dumps(club_labels),
        'club_data_json': json.dumps(club_data),
        'genre_data_json': json.dumps([hommes_count, femmes_count]),
    }
    return render(request, 'ligues/statistiques_publiques.html', context)

