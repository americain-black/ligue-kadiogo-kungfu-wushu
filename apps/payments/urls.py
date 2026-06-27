from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # GEST_CLUB
    path('examen/<int:session_pk>/soumettre/', views.soumettre_paiement_examen, name='soumettre_paiement_examen'),

    # GEST_FINANCIER
    path('examen/',                         views.liste_paiements_examen,   name='liste_paiements_examen'),
    path('examen/<int:pk>/',                views.detail_paiement_examen,   name='detail_paiement_examen'),
    path('examen/<int:pk>/valider/',        views.valider_paiement_examen,  name='valider_paiement_examen'),
    path('examen/<int:pk>/rejeter/',        views.rejeter_paiement_examen,  name='rejeter_paiement_examen'),
]
