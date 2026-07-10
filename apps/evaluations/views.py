import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.exams.models import AffectationJury, Inscription, RubriqueGrade, SessionExamen
from apps.results.models import Resultat
from .models import NoteRubrique


# ── Décorateurs ───────────────────────────────────────────────────────────────

def jury_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_jury()):
            return JsonResponse({'erreur': 'Accès réservé au Jury.'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def gest_ligue_requis(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.est_gest_ligue()):
            return JsonResponse(
                {'erreur': 'Accès réservé au Gestionnaire de Ligue.'}, status=403
            )
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Utilitaire de diffusion WebSocket ────────────────────────────────────────

def _diffuser(session_id, type_event, data):
    """Envoie un événement au groupe WebSocket de la session."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'session_{session_id}',
        {'type': type_event, 'data': data},
    )


def _verifier_et_calculer_resultat(inscription, session_id):
    """
    Vérifie si toutes les notes sont validées pour ce candidat.
    Si oui, calcule le résultat et le diffuse via WebSocket.
    Sinon, diffuse un événement 'notes_manquantes'.
    """
    rubriques_requises = RubriqueGrade.objects.filter(
        grade=inscription.grade_vise, actif=True
    )
    notes_validees = NoteRubrique.objects.filter(
        inscription=inscription, validee=True
    )

    if notes_validees.count() < rubriques_requises.count():
        jurys_manquants = [
            rg.rubrique.nom
            for rg in rubriques_requises
            if not notes_validees.filter(rubrique_grade=rg).exists()
        ]
        _diffuser(session_id, 'notes_manquantes', {
            'inscription_id': inscription.pk,
            'pratiquant': str(inscription.pratiquant),
            'rubriques_manquantes': jurys_manquants,
        })
        return

    resultat = Resultat.calculer(inscription)
    if resultat:
        _diffuser(session_id, 'resultat_calcule', {
            'inscription_id': inscription.pk,
            'pratiquant': str(inscription.pratiquant),
            'moyenne': str(resultat.moyenne),
            'decision': resultat.decision,
        })


# ── Interface Jury ────────────────────────────────────────────────────────────

@login_required
def interface_notation(request, session_id):
    """Page principale de notation pour le Jury (affiche les candidats autorisés)."""
    session = get_object_or_404(SessionExamen, pk=session_id)

    user = request.user
    est_jury = user.est_jury() and AffectationJury.objects.filter(
        session=session, jury=user
    ).exists()
    est_gl = user.is_superuser or user.est_gest_ligue()

    if not est_jury and not est_gl:
        return redirect('accounts:tableau_de_bord')

    inscriptions = (
        Inscription.objects.filter(session=session, statut='AUTORISE')
        .select_related('pratiquant', 'grade_vise')
        .prefetch_related('notes')
        .order_by('pratiquant__nom')
    )

    return render(request, 'evaluations/interface_notation.html', {
        'session': session,
        'inscriptions': inscriptions,
        'est_jury': est_jury,
        'est_gl': est_gl,
        'ws_url': f'ws/evaluations/session/{session_id}/notation/',
    })


@login_required
def detail_candidat(request, session_id, inscription_id):
    """Fiche d'un candidat avec sa grille de notation."""
    session = get_object_or_404(SessionExamen, pk=session_id)
    inscription = get_object_or_404(
        Inscription, pk=inscription_id, session=session, statut='AUTORISE'
    )

    user = request.user
    est_jury = user.est_jury() and AffectationJury.objects.filter(
        session=session, jury=user
    ).exists()
    est_gl = user.is_superuser or user.est_gest_ligue()

    if not est_jury and not est_gl:
        return redirect('accounts:tableau_de_bord')

    rubriques = RubriqueGrade.objects.filter(
        grade=inscription.grade_vise, actif=True
    ).select_related('rubrique')

    notes_existantes = {
        n.rubrique_grade_id: n
        for n in NoteRubrique.objects.filter(
            inscription=inscription, affectation__jury=user
        )
    }

    return render(request, 'evaluations/detail_candidat.html', {
        'session': session,
        'inscription': inscription,
        'rubriques': rubriques,
        'notes_existantes': notes_existantes,
        'est_jury': est_jury,
        'est_gl': est_gl,
    })


# ── Saisie et validation des notes (JSON) ────────────────────────────────────

@require_POST
@jury_requis
def saisir_note(request, session_id, inscription_id, rubrique_grade_id):
    """
    Le Jury saisit ou modifie une note (avant validation).
    Diffuse l'événement 'note_saisie' en temps réel.
    """
    try:
        data = json.loads(request.body)
        valeur = float(data['note'])
    except (KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({'erreur': 'Données invalides.'}, status=400)

    if not (0 <= valeur <= 20):
        return JsonResponse({'erreur': 'La note doit être comprise entre 0 et 20.'}, status=400)

    inscription = get_object_or_404(
        Inscription, pk=inscription_id, session_id=session_id, statut='AUTORISE'
    )
    rubrique_grade = get_object_or_404(
        RubriqueGrade, pk=rubrique_grade_id, grade=inscription.grade_vise, actif=True
    )
    affectation = get_object_or_404(
        AffectationJury, session_id=session_id, jury=request.user
    )

    note, _ = NoteRubrique.objects.get_or_create(
        inscription=inscription,
        rubrique_grade=rubrique_grade,
        defaults={'note': valeur, 'affectation': affectation},
    )

    if note.validee:
        return JsonResponse({'erreur': 'Cette note est déjà validée.'}, status=400)

    note.note = valeur
    note.save(update_fields=['note'])

    _diffuser(session_id, 'note_saisie', {
        'inscription_id': inscription.pk,
        'pratiquant': str(inscription.pratiquant),
        'rubrique': rubrique_grade.rubrique.nom,
        'note': valeur,
        'jury': str(request.user),
        'validee': False,
    })

    return JsonResponse({'statut': 'ok', 'note_id': note.pk, 'note': valeur})


@require_POST
@jury_requis
def valider_note(request, note_id):
    """
    Le Jury valide définitivement une note.
    Déclenche le calcul du résultat si toutes les notes sont présentes.
    """
    note = get_object_or_404(NoteRubrique, pk=note_id, affectation__jury=request.user)

    if note.validee:
        return JsonResponse({'erreur': 'Note déjà validée.'}, status=400)

    try:
        note.valider()
    except ValidationError as e:
        return JsonResponse({'erreur': str(e)}, status=400)

    session_id = note.inscription.session_id

    _diffuser(session_id, 'note_saisie', {
        'inscription_id': note.inscription_id,
        'pratiquant': str(note.inscription.pratiquant),
        'rubrique': note.rubrique_grade.rubrique.nom,
        'note': float(note.note),
        'jury': str(request.user),
        'validee': True,
    })

    _verifier_et_calculer_resultat(note.inscription, session_id)

    return JsonResponse({'statut': 'ok', 'note_id': note.pk})


@require_POST
@jury_requis
def demander_correction_note(request, note_id):
    """Le Jury signale une erreur sur une note validée et demande une correction."""
    note = get_object_or_404(NoteRubrique, pk=note_id, affectation__jury=request.user)

    try:
        note.demander_correction()
    except ValidationError as e:
        return JsonResponse({'erreur': str(e)}, status=400)

    return JsonResponse({'statut': 'ok', 'message': 'Demande de correction envoyée.'})


@require_POST
@gest_ligue_requis
def deverrouiller_note(request, note_id):
    """
    Le Gestionnaire Ligue autorise la correction d'une note validée.
    Diffuse le déverrouillage en temps réel.
    """
    note = get_object_or_404(NoteRubrique, pk=note_id)

    try:
        note.deverrouiller()
    except ValidationError as e:
        return JsonResponse({'erreur': str(e)}, status=400)

    session_id = note.inscription.session_id

    _diffuser(session_id, 'note_deverrouillee', {
        'note_id': note.pk,
        'inscription_id': note.inscription_id,
        'pratiquant': str(note.inscription.pratiquant),
        'rubrique': note.rubrique_grade.rubrique.nom,
        'jury': str(note.affectation.jury),
    })

    return JsonResponse({'statut': 'ok', 'message': 'Note déverrouillée.'})


# ── Tableau de bord résultats (Gestionnaire Ligue) ────────────────────────────

@gest_ligue_requis
def tableau_resultats(request, session_id):
    """
    Vue temps réel des résultats pour le Gestionnaire Ligue.
    Se connecte au même groupe WebSocket que les jurys.
    """
    session = get_object_or_404(SessionExamen, pk=session_id)

    inscriptions = (
        Inscription.objects.filter(session=session, statut='AUTORISE')
        .select_related('pratiquant', 'grade_vise')
        .prefetch_related('notes', 'resultat')
        .order_by('pratiquant__nom')
    )

    return render(request, 'evaluations/tableau_resultats.html', {
        'session': session,
        'inscriptions': inscriptions,
        'ws_url': f'ws/evaluations/session/{session_id}/notation/',
    })
