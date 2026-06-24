from django.contrib import admin
from .models import Actualite, Document


@admin.register(Actualite)
class ActualiteAdmin(admin.ModelAdmin):
    list_display   = ('titre', 'ligue', 'source', 'statut', 'date_creation')
    list_filter    = ('statut', 'source', 'ligue')
    search_fields  = ('titre', 'contenu')
    readonly_fields = ('date_creation', 'date_publication', 'validee_par')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display   = ('titre', 'ligue', 'type_document', 'est_public', 'date_publication')
    list_filter    = ('type_document', 'est_public', 'ligue')
    search_fields  = ('titre',)
    readonly_fields = ('date_publication',)
