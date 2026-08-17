from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Min
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.exams.models import Inscription, RubriqueGrade, SessionExamen
from .models import Resultat


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


def _lignes_notation(inscription):
    """Associe chaque rubrique du grade visé à la note validée du candidat (ou None)."""
    notes = {n.rubrique_grade_id: n for n in inscription.notes.filter(validee=True)}
    rubriques = RubriqueGrade.objects.filter(
        grade=inscription.grade_vise, actif=True
    ).select_related('rubrique')
    lignes = []
    for rg in rubriques:
        note = notes.get(rg.pk)
        lignes.append({
            'rubrique_grade': rg,
            'note': note,
            'pondere': (note.note * rg.coefficient) if note else None,
        })
    return lignes


def _rappel_moyennes(resultat):
    """
    Historique des résultats précédents du candidat (autres grades déjà
    passés), combinant les résultats automatiques du système et les passages
    historiques saisis manuellement.
    Garantit toujours la présence de lignes (avec complément par des lignes vides)
    afin d'afficher la grille complète avec ses bordures dans le PDF.
    """
    pratiquant = resultat.inscription.pratiquant
    precedents = (
        Resultat.objects.filter(inscription__pratiquant=pratiquant, publie=True)
        .exclude(pk=resultat.pk)
        .select_related('inscription__session', 'inscription__grade_vise')
        .order_by('-inscription__session__date_examen')
    )
    lignes = []
    for r in precedents:
        rang, total = r.rang()
        rang_str = f"{rang} Ex" if rang else "—"
        lignes.append({
            'date': r.inscription.session.date_examen,
            'grade': str(r.inscription.grade_vise),
            'moyenne': r.moyenne,
            'rang': rang_str,
            'mention': r.mention(),
        })

    # Ajout des historiques manuels s'il y en a
    for h in pratiquant.historique_passages.all():
        lignes.append({
            'date': h.date_passage,
            'grade': h.grade_libelle,
            'moyenne': h.moyenne,
            'rang': h.rang or "—",
            'mention': h.mention or "—",
        })

    # Complément pour avoir toujours un tableau de 4 lignes de quadrillage
    lignes_vides_count = max(0, 4 - len(lignes))
    lignes_vides = list(range(lignes_vides_count))

    return {
        'lignes': lignes,
        'lignes_vides': lignes_vides,
    }



def _stats_cohorte(resultat):
    """
    Moyenne, min et max de la moyenne parmi tous les candidats de la même
    session visant le même grade (toutes options confondues), pour les
    colonnes « Moy. grade / Moy. min / Moy. max » du bulletin.
    """
    inscription = resultat.inscription
    stats = Resultat.objects.filter(
        inscription__session=inscription.session,
        inscription__grade_vise=inscription.grade_vise,
    ).aggregate(moy_moyenne=Avg('moyenne'), moy_min=Min('moyenne'), moy_max=Max('moyenne'))
    return {
        'moyenne': stats['moy_moyenne'],
        'minimum': stats['moy_min'],
        'maximum': stats['moy_max'],
    }


def _peut_consulter(request, resultat):
    """Autorise : superuser, GL de la ligue concernée, GC du club du candidat (résultat publié)."""
    user = request.user
    if user.is_superuser:
        return True
    if user.est_gest_ligue():
        return resultat.inscription.session.annee_sportive.ligue_id == user.ligue_id
    if user.est_gest_club():
        club = getattr(user, 'club', None)
        return (
            club is not None
            and resultat.inscription.pratiquant.club_id == club.id
            and resultat.publie
        )
    return False


def consultation_publique(request):
    """
    Recherche publique d'un résultat par matricule (aucune connexion requise).
    Volontairement pas de recherche dynamique (suggestions à la saisie) sur
    cette page : le matricule complet doit être saisi et validé, pour éviter
    qu'on découvre des noms de candidats en essayant des matricules au hasard.
    """
    from apps.practitioners.models import Pratiquant

    matricule = request.GET.get('matricule', '').strip()
    recherche_effectuee = bool(matricule)
    pratiquant = None
    resultats  = []
    erreur     = None

    if matricule:
        pratiquant = Pratiquant.objects.select_related('club').filter(
            matricule__iexact=matricule,
        ).first()

        if pratiquant is None:
            erreur = "Aucun candidat ne correspond à ce matricule."
        else:
            resultats_qs = (
                Resultat.objects.filter(inscription__pratiquant=pratiquant, publie=True)
                .select_related('inscription__session', 'inscription__grade_vise')
                .order_by('inscription__session__date_examen')
            )
            for r in resultats_qs:
                rang, total = r.rang()
                resultats.append({
                    'resultat': r,
                    'session': r.inscription.session,
                    'grade_vise': r.inscription.grade_vise,
                    'rang': rang,
                    'total': total,
                    'mention': r.mention(),
                })
            if not resultats:
                erreur = "Aucun résultat publié pour ce candidat pour le moment."
                pratiquant = None

    return render(request, 'results/consultation_publique.html', {
        'matricule': matricule,
        'recherche_effectuee': recherche_effectuee,
        'pratiquant': pratiquant,
        'resultats': resultats,
        'erreur': erreur,
    })


@login_required
def detail_resultat(request, pk):
    resultat = get_object_or_404(
        Resultat.objects.select_related(
            'inscription__pratiquant', 'inscription__grade_vise',
            'inscription__session', 'inscription__pratiquant__club',
        ),
        pk=pk,
    )
    if not _peut_consulter(request, resultat):
        messages.error(request, "Vous n'êtes pas autorisé à consulter ce résultat.")
        return redirect('accounts:tableau_de_bord')

    inscription = resultat.inscription
    rang, total_rang = resultat.rang()

    return render(request, 'results/detail_resultat.html', {
        'resultat': resultat,
        'inscription': inscription,
        'lignes': _lignes_notation(inscription),
        'rang': rang,
        'total_rang': total_rang,
    })


@gest_club_requis
def resultats_session_club(request, session_pk):
    club = request.user.club
    session = get_object_or_404(
        SessionExamen, pk=session_pk, annee_sportive__ligue=club.ligue
    )
    inscriptions = (
        Inscription.objects.filter(
            session=session, pratiquant__club=club, resultat__publie=True
        )
        .select_related('pratiquant', 'grade_vise', 'resultat')
        .order_by('pratiquant__nom')
    )
    for insc in inscriptions:
        insc.rang, insc.total_rang = insc.resultat.rang()

    return render(request, 'results/resultats_session_club.html', {
        'session': session,
        'club': club,
        'inscriptions': inscriptions,
    })


@login_required
def telecharger_bulletin(request, pk):
    resultat = get_object_or_404(
        Resultat.objects.select_related(
            'inscription__pratiquant', 'inscription__grade_vise',
            'inscription__session__annee_sportive__ligue',
            'inscription__pratiquant__club',
        ),
        pk=pk,
    )
    if not _peut_consulter(request, resultat):
        messages.error(request, "Vous n'êtes pas autorisé à télécharger ce bulletin.")
        return redirect('accounts:tableau_de_bord')

    from weasyprint import HTML

    inscription = resultat.inscription
    rang, total_rang = resultat.rang()
    lignes = _lignes_notation(inscription)
    total_coeff   = sum(l['rubrique_grade'].coefficient for l in lignes)
    total_pondere = sum(l['pondere'] for l in lignes if l['pondere'] is not None)

    html_string = render(request, 'results/bulletin_pdf.html', {
        'resultat': resultat,
        'inscription': inscription,
        'ligue': inscription.session.annee_sportive.ligue,
        'lignes': lignes,
        'total_coeff': total_coeff,
        'total_pondere': total_pondere,
        'rang': rang,
        'total_rang': total_rang,
        'rappel': _rappel_moyennes(resultat),
        'stats': _stats_cohorte(resultat),
    }).content.decode('utf-8')

    pdf_bytes = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

    nom_fichier = f"bulletin_{inscription.pratiquant.nom}_{inscription.pratiquant.prenom}.pdf".replace(' ', '_')
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
    return response


def gest_ligue_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_ligue()):
            messages.error(request, "Accès réservé au Gestionnaire de Ligue.")
            return redirect('accounts:tableau_de_bord')
        return view_func(request, *args, **kwargs)
    return wrapper


@gest_ligue_requis
def liste_resultats_ligue(request):
    """
    Interface du gestionnaire ligue pour consulter la liste de tous les résultats,
    filtrer par Session, par Club ou par Décision, et lancer des impressions groupées.
    """
    from apps.clubs.models import Club
    from django.db.models import Q

    ligue = getattr(request.user, 'ligue', None)
    if not ligue and request.user.is_superuser:
        from apps.ligues.models import Ligue
        ligue = Ligue.objects.first()

    sessions = SessionExamen.objects.filter(annee_sportive__ligue=ligue).order_by('-date_examen')
    clubs = Club.objects.filter(ligue=ligue).order_by('nom_club')

    session_id = request.GET.get('session')
    club_id    = request.GET.get('club')
    decision   = request.GET.get('decision')
    q          = request.GET.get('q', '').strip()

    resultats_qs = Resultat.objects.filter(
        inscription__session__annee_sportive__ligue=ligue
    ).select_related(
        'inscription__pratiquant',
        'inscription__pratiquant__club',
        'inscription__grade_vise',
        'inscription__option',
        'inscription__session'
    ).order_by('inscription__grade_vise__id_grade', '-moyenne', 'inscription__pratiquant__nom', 'inscription__pratiquant__prenom')

    if session_id:
        resultats_qs = resultats_qs.filter(inscription__session_id=session_id)
    if club_id:
        resultats_qs = resultats_qs.filter(inscription__pratiquant__club_id=club_id)
    if decision:
        resultats_qs = resultats_qs.filter(decision=decision)
    if q:
        resultats_qs = resultats_qs.filter(
            Q(inscription__pratiquant__nom__icontains=q) |
            Q(inscription__pratiquant__prenom__icontains=q) |
            Q(inscription__pratiquant__matricule__icontains=q)
        )

    resultats_data = []
    for r in resultats_qs:
        rang, total = r.rang()
        resultats_data.append({
            'resultat': r,
            'rang': rang,
            'total': total,
        })

    return render(request, 'results/liste_resultats_ligue.html', {
        'sessions': sessions,
        'clubs': clubs,
        'session_id': session_id,
        'club_id': club_id,
        'decision': decision,
        'q': q,
        'resultats_data': resultats_data,
        'total_count': len(resultats_data),
    })


@gest_ligue_requis
def impression_groupee_bulletins(request):
    """
    Génère un document PDF unique contenant tous les bulletins sélectionnés
    ou tous les bulletins correspondant aux filtres actifs (Session / Club).
    """
    from weasyprint import HTML
    from django.db.models import Q

    ligue = getattr(request.user, 'ligue', None)
    if not ligue and request.user.is_superuser:
        from apps.ligues.models import Ligue
        ligue = Ligue.objects.first()

    ids_selectionnes = request.POST.getlist('resultats_ids') or request.GET.getlist('ids')
    session_id       = request.GET.get('session') or request.POST.get('session')
    club_id          = request.GET.get('club') or request.POST.get('club')

    resultats_qs = Resultat.objects.filter(
        inscription__session__annee_sportive__ligue=ligue
    ).select_related(
        'inscription__pratiquant',
        'inscription__pratiquant__club',
        'inscription__grade_vise',
        'inscription__option',
        'inscription__session',
        'inscription__session__annee_sportive__ligue'
    ).order_by('inscription__pratiquant__club__nom_club', 'inscription__pratiquant__nom')

    if ids_selectionnes:
        resultats_qs = resultats_qs.filter(id__in=ids_selectionnes)
    else:
        if session_id:
            resultats_qs = resultats_qs.filter(inscription__session_id=session_id)
        if club_id:
            resultats_qs = resultats_qs.filter(inscription__pratiquant__club_id=club_id)

    if not resultats_qs.exists():
        messages.error(request, "Aucun bulletin à imprimer pour la sélection ou le filtre actif.")
        return redirect('results:liste_resultats_ligue')

    bulletins_items = []
    for r in resultats_qs:
        insc = r.inscription
        rang, total_rang = r.rang()
        lignes = _lignes_notation(insc)
        total_coeff   = sum(l['rubrique_grade'].coefficient for l in lignes)
        total_pondere = sum(l['pondere'] for l in lignes if l['pondere'] is not None)
        bulletins_items.append({
            'resultat': r,
            'inscription': insc,
            'ligue': insc.session.annee_sportive.ligue,
            'lignes': lignes,
            'total_coeff': total_coeff,
            'total_pondere': total_pondere,
            'rang': rang,
            'total_rang': total_rang,
            'rappel': _rappel_moyennes(r),
            'stats': _stats_cohorte(r),
        })

    html_string = render(request, 'results/bulletins_groupe_pdf.html', {
        'bulletins_items': bulletins_items,
        'ligue': ligue,
    }).content.decode('utf-8')

    pdf_bytes = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="bulletins_groupe_impression.pdf"'
    return response
