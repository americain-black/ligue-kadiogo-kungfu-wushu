from django.urls import path
from . import views

app_name = 'ligues'

urlpatterns = [
    path('',                          views.liste_ligues,        name='liste'),
    path('creer/',                    views.creer_ligue,         name='creer'),
    path('<int:pk>/modifier/',        views.modifier_ligue,      name='modifier'),
    path('<int:pk>/toggle-statut/',   views.toggle_statut_ligue, name='toggle_statut'),
    path('<int:pk>/supprimer/',       views.supprimer_ligue,     name='supprimer'),

    # Organigramme
    path('organigramme/',                              views.organigramme,        name='organigramme'),
    path('organigramme/volet/creer/',                  views.creer_volet,         name='creer_volet'),
    path('organigramme/volet/<int:pk>/modifier/',      views.modifier_volet,      name='modifier_volet'),
    path('organigramme/volet/<int:pk>/supprimer/',     views.supprimer_volet,     name='supprimer_volet'),
    path('organigramme/volet/<int:volet_pk>/membre/ajouter/', views.ajouter_membre, name='ajouter_membre'),
    path('organigramme/membre/<int:pk>/modifier/',     views.modifier_membre,     name='modifier_membre'),
    path('organigramme/membre/<int:pk>/toggle/',     views.toggle_actif_membre, name='toggle_actif_membre'),
    path('organigramme/membre/<int:pk>/supprimer/', views.supprimer_membre,    name='supprimer_membre'),
]
