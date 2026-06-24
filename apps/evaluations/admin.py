from django.contrib import admin
from .models import NoteRubrique


@admin.register(NoteRubrique)
class NoteRubriqueAdmin(admin.ModelAdmin):
    list_display   = (
        'inscription', 'rubrique_grade', 'jury', 'note', 'validee', 'date_saisie'
    )
    list_filter    = ('validee', 'jury', 'rubrique_grade__rubrique')
    search_fields  = (
        'inscription__pratiquant__nom',
        'inscription__pratiquant__prenom'
    )
    readonly_fields = ('date_saisie', 'date_validation')
