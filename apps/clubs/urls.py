
# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    # Annuaire public des clubs
    path('annuaire/',                     views.annuaire_clubs,       name='annuaire'),

    path('',                              views.liste_clubs,          name='liste'),
    path('creer/',                        views.creer_club,           name='creer'),
    path('exporter/',                     views.exporter_clubs,       name='exporter'),
    path('importer/',                     views.importer_clubs,       name='importer'),
    path('telecharger-modele/',           views.telecharger_modele_clubs, name='telecharger_modele'),
    path('<int:pk>/',                     views.detail_club,          name='detail'),
    path('<int:pk>/modifier/',            views.modifier_club,        name='modifier'),
    path('<int:pk>/toggle-statut/',        views.toggle_statut_club,   name='toggle_statut'),
    path('<int:pk>/supprimer/',           views.supprimer_club,       name='supprimer'),
    path('affiliations/',                 views.demandes_affiliation, name='demandes_affiliation'),
    path('affiliations/historique/',      views.historique_affiliations_ligue, name='historique_affiliations'),
    path('affiliations/modele-attestation/', views.gerer_modele_attestation, name='modele_attestation'),
    path('affiliations/parametres/',       views.gerer_parametres_affiliation, name='parametres_affiliation'),
    path('affiliations/<int:pk>/',         views.detail_demande_affiliation, name='detail_demande_affiliation'),
    path('affiliations/<int:pk>/valider/', views.valider_demande,     name='valider_demande'),
    path('affiliations/<int:pk>/rejeter/', views.rejeter_demande,     name='rejeter_demande'),
    path('affiliations/<int:pk>/attestation/', views.attestation_affiliation, name='attestation_affiliation'),

    # Affiliation — côté Gestionnaire de Club
    path('mon-affiliation/',                        views.mon_affiliation,           name='mon_affiliation'),
    path('mon-affiliation/historique/',             views.historique_affiliations_club, name='mes_demandes_affiliation'),
    path('mon-affiliation/recepisse/enregistrer/',   views.enregistrer_recepisse_club,  name='enregistrer_recepisse_club'),
    path('mon-affiliation/demarrer/',                views.demarrer_demande_affiliation, name='demarrer_demande_affiliation'),
    path('mon-affiliation/piece/ajouter/',           views.ajouter_piece_affiliation,  name='ajouter_piece_affiliation'),
    path('mon-affiliation/piece/<int:pk>/supprimer/', views.supprimer_piece_affiliation, name='supprimer_piece_affiliation'),

    # Organigramme club
    path('<int:club_pk>/organigramme/',                              views.organigramme_club,        name='organigramme'),
    path('<int:club_pk>/organigramme/visuel/',                       views.organigramme_visuel_club, name='organigramme_visuel'),
    path('organigramme/volet/<int:volet_pk>/membre/ajouter/',        views.ajouter_membre_club,      name='ajouter_membre_club'),
    path('organigramme/membre/<int:pk>/modifier/',                   views.modifier_membre_club,     name='modifier_membre_club'),
    path('organigramme/membre/<int:pk>/toggle/',     views.toggle_actif_membre_club, name='toggle_actif_membre_club'),
    path('organigramme/membre/<int:pk>/supprimer/', views.supprimer_membre_club,    name='supprimer_membre_club'),
]
