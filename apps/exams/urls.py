from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    # ── Années sportives ──────────────────────────────────────────────────────
    path('annees-sportives/',                 views.liste_annees_sportives,  name='annees_sportives'),
    path('annees-sportives/creer/',           views.creer_annee_sportive,    name='creer_annee_sportive'),
    path('annees-sportives/<int:pk>/modifier/', views.modifier_annee_sportive, name='modifier_annee_sportive'),
    path('annees-sportives/<int:pk>/cloturer/', views.cloturer_annee_sportive,  name='cloturer_annee_sportive'),
    path('annees-sportives/<int:pk>/supprimer/', views.supprimer_annee_sportive, name='supprimer_annee_sportive'),
    path('annees-sportives/<int:annee_pk>/tarifs/', views.liste_tarifs,   name='tarifs'),
    path('tarifs/',                                 views.tarifs_accueil,  name='tarifs_accueil'),
    path('tarifs/<int:pk>/modifier/',              views.modifier_tarif,  name='modifier_tarif'),
    path('tarifs/<int:pk>/supprimer/',             views.supprimer_tarif, name='supprimer_tarif'),

    # ── Rubriques / Épreuves ──────────────────────────────────────────────────
    path('rubriques/',                             views.liste_rubriques,           name='rubriques'),
    path('rubriques/<int:pk>/modifier/',           views.modifier_rubrique,         name='modifier_rubrique'),
    path('rubriques/<int:pk>/toggle-actif/',       views.toggle_actif_rubrique,     name='toggle_actif_rubrique'),
    path('rubriques/<int:pk>/supprimer/',          views.supprimer_rubrique,        name='supprimer_rubrique'),
    path('rubriques/<int:pk>/grades/',             views.config_rubrique_grades,    name='config_rubrique_grades'),
    path('rubrique-grades/<int:pk>/modifier/',     views.modifier_rubrique_grade,   name='modifier_rubrique_grade'),
    path('rubrique-grades/<int:pk>/toggle-actif/', views.toggle_actif_rubrique_grade, name='toggle_actif_rubrique_grade'),
    path('rubrique-grades/<int:pk>/supprimer/',    views.supprimer_rubrique_grade,  name='supprimer_rubrique_grade'),

    # ── Options d'examen ─────────────────────────────────────────────────────
    path('options/',                               views.liste_options,           name='options'),
    path('options/<int:pk>/modifier/',             views.modifier_option,         name='modifier_option'),
    path('options/<int:pk>/toggle-actif/',         views.toggle_actif_option,     name='toggle_actif_option'),
    path('options/<int:pk>/supprimer/',            views.supprimer_option,        name='supprimer_option'),

    # ── Modèle de matricule ───────────────────────────────────────────────────
    path('matricule/',                             views.gerer_modele_matricule,  name='modele_matricule'),
    path('matricule/supprimer/',                   views.supprimer_modele_matricule, name='supprimer_modele_matricule'),

    # ── GEST_LIGUE ────────────────────────────────────────────────────────────
    path('',                                  views.liste_sessions,        name='liste'),
    path('creer/',                            views.creer_session,         name='creer'),
    path('<int:pk>/',                         views.detail_session,        name='detail'),
    path('<int:pk>/modifier/',                views.modifier_session,      name='modifier'),
    path('<int:pk>/ouvrir-inscriptions/',     views.ouvrir_inscriptions,   name='ouvrir_inscriptions'),
    path('<int:pk>/cloturer-inscriptions/',   views.cloturer_inscriptions, name='cloturer_inscriptions'),
    path('<int:pk>/demarrer/',                views.demarrer_session,      name='demarrer'),
    path('<int:pk>/supprimer/',               views.supprimer_session,     name='supprimer'),
    path('<int:pk>/affecter-jury/',           views.affecter_jury,         name='affecter_jury'),
    path('jury/<int:pk>/retirer/',            views.retirer_jury,          name='retirer_jury'),
    path('<int:session_pk>/valider-club/<int:club_pk>/', views.valider_liste_club, name='valider_liste_club'),

    # ── GEST_CLUB ─────────────────────────────────────────────────────────────
    path('club/sessions/',                         views.sessions_ouvertes,         name='club_sessions'),
    path('club/<int:session_pk>/inscriptions/',    views.session_inscriptions_club, name='club_inscriptions'),
    path('club/<int:session_pk>/inscrire/',        views.inscrire_pratiquant,       name='inscrire'),
    path('inscriptions/<int:pk>/supprimer/',       views.supprimer_inscription,     name='supprimer_inscription'),
]
