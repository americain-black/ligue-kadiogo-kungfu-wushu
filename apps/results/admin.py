from django.contrib import admin
from .models import Resultat


@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display    = (
        'inscription', 'moyenne', 'decision', 'publie', 'date_calcul'
    )
    list_filter     = ('decision', 'publie', 'inscription__session')
    search_fields   = (
        'inscription__pratiquant__nom',
        'inscription__pratiquant__prenom'
    )
    readonly_fields = ('date_calcul', 'date_publication', 'moyenne', 'decision')
