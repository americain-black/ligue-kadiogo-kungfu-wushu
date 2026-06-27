from django.urls import path
from . import views

app_name = 'practitioners'

urlpatterns = [
    # Pratiquants
    path('',                      views.liste_pratiquants,    name='liste'),
    path('ajouter/',              views.ajouter_pratiquant,   name='ajouter'),
    path('<int:pk>/',             views.detail_pratiquant,    name='detail'),
    path('<int:pk>/modifier/',    views.modifier_pratiquant,  name='modifier'),
    path('<int:pk>/toggle/',      views.toggle_actif_pratiquant, name='toggle_actif'),
    path('<int:pk>/supprimer/',   views.supprimer_pratiquant,    name='supprimer'),

    # Grades (GEST_LIGUE)
    path('grades/',                        views.liste_grades,       name='grades'),
    path('grades/creer/',                  views.creer_grade,        name='creer_grade'),
    path('grades/<int:pk>/modifier/',      views.modifier_grade,     name='modifier_grade'),
    path('grades/<int:pk>/supprimer/',     views.supprimer_grade,    name='supprimer_grade'),
    path('grades/<int:pk>/toggle/',        views.toggle_actif_grade, name='toggle_actif_grade'),
]
