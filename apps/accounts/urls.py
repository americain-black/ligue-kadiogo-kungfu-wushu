from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('connexion/',       views.connexion,   name='login'),
    path('deconnexion/',     views.deconnexion, name='logout'),

    # Redirection selon rôle
    path('tableau-de-bord/', views.tableau_de_bord, name='tableau_de_bord'),

    # Dashboards par rôle
    path('super-admin/',     views.dashboard_super_admin, name='dashboard_super_admin'),
    path('ligue/',           views.dashboard_ligue,       name='dashboard_ligue'),
    path('club/',            views.dashboard_club,        name='dashboard_club'),
    path('financier/',       views.dashboard_financier,   name='dashboard_financier'),
    path('jury/',            views.dashboard_jury,        name='dashboard_jury'),

    # Gestion des utilisateurs (Super Admin)
    path('utilisateurs/',                          views.liste_utilisateurs,       name='liste_utilisateurs'),
    path('utilisateurs/creer/',                    views.creer_utilisateur,        name='creer_utilisateur'),
    path('utilisateurs/<int:pk>/modifier/',        views.modifier_utilisateur,     name='modifier_utilisateur'),
    path('utilisateurs/<int:pk>/roles/',           views.gerer_roles,              name='gerer_roles'),
    path('utilisateurs/<int:pk>/toggle-statut/',   views.toggle_statut_utilisateur,name='toggle_statut_utilisateur'),
]
