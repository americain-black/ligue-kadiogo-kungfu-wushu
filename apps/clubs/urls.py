from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    path('',                              views.liste_clubs,          name='liste'),
    path('creer/',                        views.creer_club,           name='creer'),
    path('<int:pk>/',                     views.detail_club,          name='detail'),
    path('<int:pk>/modifier/',            views.modifier_club,        name='modifier'),
    path('<int:pk>/toggle-statut/',        views.toggle_statut_club,   name='toggle_statut'),
    path('<int:pk>/supprimer/',           views.supprimer_club,       name='supprimer'),
    path('affiliations/',                 views.demandes_affiliation, name='demandes_affiliation'),
    path('affiliations/<int:pk>/valider/', views.valider_demande,     name='valider_demande'),
    path('affiliations/<int:pk>/rejeter/', views.rejeter_demande,     name='rejeter_demande'),

    # Organigramme club
    path('<int:club_pk>/organigramme/',                              views.organigramme_club,        name='organigramme'),
    path('<int:club_pk>/organigramme/volet/creer/',                  views.creer_volet_club,         name='creer_volet_club'),
    path('organigramme/volet/<int:pk>/modifier/',                    views.modifier_volet_club,      name='modifier_volet_club'),
    path('organigramme/volet/<int:pk>/supprimer/',                   views.supprimer_volet_club,     name='supprimer_volet_club'),
    path('organigramme/volet/<int:volet_pk>/membre/ajouter/',        views.ajouter_membre_club,      name='ajouter_membre_club'),
    path('organigramme/membre/<int:pk>/modifier/',                   views.modifier_membre_club,     name='modifier_membre_club'),
    path('organigramme/membre/<int:pk>/toggle/',     views.toggle_actif_membre_club, name='toggle_actif_membre_club'),
    path('organigramme/membre/<int:pk>/supprimer/', views.supprimer_membre_club,    name='supprimer_membre_club'),
]
