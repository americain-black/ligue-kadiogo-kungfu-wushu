from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # GEST_CLUB
    path('examen/<int:session_pk>/soumettre/', views.soumettre_paiement_examen, name='soumettre_paiement_examen'),
    path('affiliation/soumettre/',             views.soumettre_paiement_affiliation, name='soumettre_paiement_affiliation'),

    # GEST_LIGUE
    path('valides/',             views.paiements_valides_accueil,        name='paiements_valides_accueil'),
    path('examen/valides/',      views.paiements_valides_gl,             name='paiements_valides_gl'),
    path('affiliation/valides/', views.paiements_valides_affiliation_gl, name='paiements_valides_affiliation_gl'),

    # GEST_FINANCIER
    path('historique/',                     views.historique_paiements_accueil, name='historique_paiements_accueil'),

    # GEST_FINANCIER — droits d'examen
    path('examen/',                         views.liste_paiements_examen,   name='liste_paiements_examen'),
    path('examen/<int:pk>/',                views.detail_paiement_examen,   name='detail_paiement_examen'),
    path('examen/<int:pk>/valider/',        views.valider_paiement_examen,      name='valider_paiement_examen'),
    path('examen/<int:pk>/insuffisant/',   views.insuffisant_paiement_examen,  name='insuffisant_paiement_examen'),
    path('examen/<int:pk>/rejeter/',       views.rejeter_paiement_examen,      name='rejeter_paiement_examen'),
    path('examen/historique/',             views.historique_paiements_examen,  name='historique_paiements_examen'),

    # GEST_FINANCIER — frais d'affiliation
    path('affiliation/',                    views.liste_paiements_affiliation,  name='liste_paiements_affiliation'),
    path('affiliation/<int:pk>/',           views.detail_paiement_affiliation,  name='detail_paiement_affiliation'),
    path('affiliation/<int:pk>/valider/',   views.valider_paiement_affiliation, name='valider_paiement_affiliation'),
    path('affiliation/<int:pk>/rejeter/',   views.rejeter_paiement_affiliation, name='rejeter_paiement_affiliation'),
    path('affiliation/historique/',         views.historique_paiements_affiliation, name='historique_paiements_affiliation'),
]
