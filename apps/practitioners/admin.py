from django.contrib import admin
from .models import Grade, Pratiquant


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display  = ('id_grade', 'nom', 'actif')
    list_filter   = ('actif',)
    ordering      = ('id_grade',)


@admin.register(Pratiquant)
class PratiquantAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'prenom', 'club', 'grade_actuel', 'sexe', 'actif')
    list_filter   = ('actif', 'sexe', 'grade_actuel', 'club__ligue')
    search_fields = ('nom', 'prenom', 'club__nom_club')
    ordering      = ('nom', 'prenom')
