from django.urls import path
from . import views

app_name = 'ligues'

urlpatterns = [
    path('',                          views.liste_ligues,        name='liste'),
    path('creer/',                    views.creer_ligue,         name='creer'),
    path('<int:pk>/modifier/',        views.modifier_ligue,      name='modifier'),
    path('<int:pk>/toggle-statut/',   views.toggle_statut_ligue, name='toggle_statut'),
]
