from django.urls import path
from . import views

app_name = 'practitioners'

urlpatterns = [
    path('',                      views.liste_pratiquants,    name='liste'),
    path('ajouter/',              views.ajouter_pratiquant,   name='ajouter'),
    path('<int:pk>/',             views.detail_pratiquant,    name='detail'),
    path('<int:pk>/modifier/',    views.modifier_pratiquant,  name='modifier'),
    path('<int:pk>/toggle/',      views.toggle_actif_pratiquant, name='toggle_actif'),
    path('<int:pk>/supprimer/',   views.supprimer_pratiquant,    name='supprimer'),
]
