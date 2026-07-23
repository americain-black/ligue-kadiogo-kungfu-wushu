from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Page d'accueil publique
    path('',                 views.accueil,     name='accueil'),

    # Authentification
    path('connexion/',       views.connexion,   name='login'),
    path('deconnexion/',     views.deconnexion, name='logout'),

    # Récupération de mot de passe
    path('mot-de-passe-oublie/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset_form.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/mot-de-passe-oublie/envoye/',
         ),
         name='password_reset'),
    path('mot-de-passe-oublie/envoye/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html',
         ),
         name='password_reset_done'),
    path('reinitialiser/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/reinitialiser/termine/',
         ),
         name='password_reset_confirm'),
    path('reinitialiser/termine/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),

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
    path('utilisateurs/<int:pk>/supprimer/',       views.supprimer_utilisateur,    name='supprimer_utilisateur'),
]
