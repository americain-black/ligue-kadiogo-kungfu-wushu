from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    # Public
    path('actualites/',            views.liste_actualites_publique,  name='actualites_publiques'),
    path('actualites/<int:pk>/',   views.detail_actualite_publique,  name='detail_actualite_publique'),
    path('documents/',             views.liste_documents_publique,   name='documents_publics'),
    path('documents/<int:pk>/apercu/', views.apercu_document,        name='apercu_document'),

    # Gestion — Ligue : actualités
    path('gestion/actualites/',                       views.liste_actualites,     name='liste_actualites'),
    path('gestion/actualites/creer/',                 views.creer_actualite,      name='creer_actualite'),
    path('gestion/actualites/<int:pk>/',              views.detail_actualite,     name='detail_actualite'),
    path('gestion/actualites/<int:pk>/modifier/',     views.modifier_actualite,   name='modifier_actualite'),
    path('gestion/actualites/<int:pk>/supprimer/',    views.supprimer_actualite,  name='supprimer_actualite'),
    path('gestion/actualites/<int:pk>/publier/',      views.publier_actualite,    name='publier_actualite'),
    path('gestion/actualites/<int:pk>/visibilite/',   views.toggle_visibilite_actualite, name='toggle_visibilite_actualite'),
    path('gestion/actualites/<int:pk>/rejeter/',      views.rejeter_actualite,    name='rejeter_actualite'),

    # Gestion — Ligue : documents
    path('gestion/documents/',                    views.liste_documents,    name='liste_documents'),
    path('gestion/documents/creer/',              views.creer_document,     name='creer_document'),
    path('gestion/documents/<int:pk>/modifier/',  views.modifier_document,  name='modifier_document'),
    path('gestion/documents/<int:pk>/supprimer/', views.supprimer_document, name='supprimer_document'),

    # Gestion — Club : mes actualités
    path('mes-actualites/',                     views.mes_actualites,             name='mes_actualites'),
    path('mes-actualites/creer/',               views.creer_actualite_club,       name='creer_actualite_club'),
    path('mes-actualites/<int:pk>/',            views.detail_actualite_club,      name='detail_actualite_club'),
    path('mes-actualites/<int:pk>/modifier/',   views.modifier_actualite_club,    name='modifier_actualite_club'),
    path('mes-actualites/<int:pk>/soumettre/',  views.soumettre_actualite_club,   name='soumettre_actualite_club'),
    path('mes-actualites/<int:pk>/supprimer/',  views.supprimer_actualite_club,   name='supprimer_actualite_club'),
]
