from django.contrib import admin
from .models import Ligue


@admin.register(Ligue)
class LigueAdmin(admin.ModelAdmin):
    list_display  = ('sigle', 'nom_ligue', 'region', 'statut', 'date_creation')
    list_filter   = ('statut', 'region')
    search_fields = ('nom_ligue', 'sigle')
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom_ligue', 'sigle', 'region', 'logo', 'statut')
        }),
        ('Contacts', {
            'fields': ('adresse_siege', 'email_contact', 'telephone')
        }),
        ('Responsables', {
            'fields': (
                'nom_directeur_adm', 'nom_directeur_tech',
                'nom_secretaire', 'contact_secretaire'
            )
        }),
    )
