from django.urls import path
from . import views

app_name = 'ligues'

urlpatterns = [
    path('',                          views.liste_ligues,        name='liste'),
    path('creer/',                    views.creer_ligue,         name='creer'),
    path('<int:pk>/modifier/',        views.modifier_ligue,      name='modifier'),
    path('<int:pk>/toggle-statut/',   views.toggle_actif_ligue,  name='toggle_statut'),

    # Organigramme
    path('organigramme/',                              views.organigramme,        name='organigramme'),
    path('organigramme/visuel/',                        views.organigramme_visuel, name='organigramme_visuel'),
    path('organigramme/volet/creer/',                  views.ajouter_volet,       name='creer_volet'),
    path('organigramme/volet/<int:pk>/modifier/',      views.modifier_volet,      name='modifier_volet'),
    path('organigramme/volet/<int:pk>/supprimer/',     views.supprimer_volet,     name='supprimer_volet'),
    path('organigramme/volet/<int:volet_pk>/membre/ajouter/', views.ajouter_membre, name='ajouter_membre'),
    path('organigramme/membre/<int:pk>/modifier/',     views.modifier_membre,     name='modifier_membre'),
    path('organigramme/membre/<int:pk>/supprimer/',    views.supprimer_membre,    name='supprimer_membre'),
    path('organigramme/membre/<int:pk>/toggle-statut/', views.toggle_actif_membre, name='toggle_actif_membre'),

    # Édition des informations "À propos" et de la présentation
    path('editer-infos/', views.editer_infos_ligue, name='editer_infos'),

    # Module de Reporting & Analytics
    path('reporting/',           views.reporting_dashboard, name='reporting_dashboard'),
    path('reporting/export-pdf/', views.export_rapport_pdf,  name='export_rapport_pdf'),
    path('statistiques-publiques/', views.statistiques_publiques, name='statistiques_publiques'),
    path('statistiques_publiques/', views.statistiques_publiques),
]
