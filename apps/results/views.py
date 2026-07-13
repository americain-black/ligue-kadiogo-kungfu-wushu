from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
    return [{'rubrique_grade': rg, 'note': notes.get(rg.pk)} for rg in rubriques]


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

    return render(request, 'results/detail_resultat.html', {
        'resultat': resultat,
        'inscription': inscription,
        'lignes': _lignes_notation(inscription),
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

    html_string = render(request, 'results/bulletin_pdf.html', {
        'resultat': resultat,
        'inscription': inscription,
        'lignes': _lignes_notation(inscription),
    }).content.decode('utf-8')

    pdf_bytes = HTML(string=html_string).write_pdf()

    nom_fichier = f"bulletin_{inscription.pratiquant.nom}_{inscription.pratiquant.prenom}.pdf".replace(' ', '_')
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
    return response
