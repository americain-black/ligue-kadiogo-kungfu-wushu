from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    path('consulter/', views.consultation_publique, name='consultation_publique'),
    path('session/<int:session_pk>/club/', views.resultats_session_club, name='resultats_session_club'),
    path('<int:pk>/', views.detail_resultat, name='detail'),
    path('<int:pk>/bulletin/', views.telecharger_bulletin, name='bulletin_pdf'),
]
