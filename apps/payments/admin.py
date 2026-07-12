from django.contrib import admin
from .models import PaiementAffiliation, PaiementExamen


@admin.register(PaiementAffiliation)
class PaiementAffiliationAdmin(admin.ModelAdmin):
    list_display   = (
        'demande', 'mode_paiement', 'montant_paye', 'reference', 'statut', 'date_soumission'
    )
    list_filter    = ('statut',)
    search_fields  = ('demande__club__nom_club', 'reference')
    readonly_fields = ('date_soumission', 'date_validation', 'valide_par')


@admin.register(PaiementExamen)
class PaiementExamenAdmin(admin.ModelAdmin):
    list_display   = (
        'club', 'session', 'montant_paye', 'montant_attendu', 'statut', 'date_soumission'
    )
    list_filter    = ('statut', 'session')
    search_fields  = ('club__nom_club', 'reference')
    readonly_fields = ('date_soumission', 'date_validation', 'valide_par')
