from django.contrib import admin
from django.utils.html import format_html
from .models import Club, DemandeAffiliation, PieceJustificativeAffiliation


class PieceJustificativeInline(admin.TabularInline):
    """
    Affiche les pièces jointes directement
    dans le formulaire de la demande d'affiliation.
    """
    model           = PieceJustificativeAffiliation
    extra           = 1       # 1 ligne vide par défaut pour ajouter
    fields          = ('type_piece', 'fichier', 'apercu', 'date_upload')
    readonly_fields = ('apercu', 'date_upload')

    def apercu(self, obj):
        """Affiche un lien de téléchargement si le fichier existe."""
        if obj.fichier:
            return format_html(
                '<a href="{}" target="_blank">📄 Voir le fichier</a>',
                obj.fichier.url
            )
        return "Aucun fichier"
    apercu.short_description = "Aperçu"


class DemandeAffiliationInline(admin.TabularInline):
    model           = DemandeAffiliation
    extra           = 0
    fields          = (
        'annee_sportive', 'statut_affiliation',
        'montant_frais', 'date_demande'
    )
    readonly_fields = ('date_demande',)
    show_change_link = True   # lien vers le détail de la demande


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display   = (
        'nom_club', 'sigle_club', 'ligue',
        'localite', 'statut_club', 'date_creation'
    )
    list_filter    = ('statut_club', 'ligue')
    search_fields  = ('nom_club', 'sigle_club', 'responsable_club')
    inlines        = [DemandeAffiliationInline]
    fieldsets = (
        ('Informations du club', {
            'fields': (
                'ligue', 'nom_club', 'sigle_club',
                'localite', 'adresse', 'telephone', 'email'
            )
        }),
        ('Responsables', {
            'fields': (
                'maitre_club',      'contact_maitre',
                'responsable_club', 'contact_responsable'
            )
        }),
        ('Compte & Statut', {
            'fields': ('utilisateur', 'statut_club')
        }),
    )


@admin.register(DemandeAffiliation)
class DemandeAffiliationAdmin(admin.ModelAdmin):
    list_display    = (
        'club', 'annee_sportive', 'statut_affiliation',
        'montant_frais', 'nb_pieces', 'date_demande'
    )
    list_filter     = ('statut_affiliation', 'annee_sportive', 'club__ligue')
    search_fields   = ('club__nom_club',)
    readonly_fields = ('date_demande',)
    inlines         = [PieceJustificativeInline]
    fieldsets = (
        ('Informations de la demande', {
            'fields': (
                'club', 'annee_sportive',
                'montant_frais', 'date_demande'
            )
        }),
        ('Décision', {
            'fields': ('statut_affiliation', 'motif_rejet')
        }),
    )

    def nb_pieces(self, obj):
        """Affiche le nombre de pièces jointes."""
        nb = obj.pieces_justificatives.count()
        couleur = 'green' if nb > 0 else 'red'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{} fichier(s)</span>',
            couleur, nb
        )
    nb_pieces.short_description = "Pièces jointes"


@admin.register(PieceJustificativeAffiliation)
class PieceJustificativeAdmin(admin.ModelAdmin):
    list_display    = (
        'demande', 'type_piece', 'nom_fichier',
        'lien_fichier', 'date_upload'
    )
    list_filter     = ('type_piece',)
    readonly_fields = ('date_upload', 'nom_fichier')

    def lien_fichier(self, obj):
        if obj.fichier:
            return format_html(
                '<a href="{}" target="_blank">📄 Télécharger</a>',
                obj.fichier.url
            )
        return "—"
    lien_fichier.short_description = "Fichier"