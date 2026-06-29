from django.urls import path
from . import views

app_name = 'evaluations'

urlpatterns = [
    # ── Interface Jury ────────────────────────────────────────────────────────
    path('session/<int:session_id>/',
         views.interface_notation, name='interface_notation'),
    path('session/<int:session_id>/candidat/<int:inscription_id>/',
         views.detail_candidat, name='detail_candidat'),

    # ── Saisie / validation des notes (JSON) ─────────────────────────────────
    path('session/<int:session_id>/candidat/<int:inscription_id>/rubrique/<int:rubrique_grade_id>/saisir/',
         views.saisir_note, name='saisir_note'),
    path('note/<int:note_id>/valider/',
         views.valider_note, name='valider_note'),
    path('note/<int:note_id>/demander-correction/',
         views.demander_correction_note, name='demander_correction_note'),
    path('note/<int:note_id>/deverrouiller/',
         views.deverrouiller_note, name='deverrouiller_note'),

    # ── Tableau résultats temps réel (Gestionnaire Ligue) ────────────────────
    path('session/<int:session_id>/resultats/',
         views.tableau_resultats, name='tableau_resultats'),
]
