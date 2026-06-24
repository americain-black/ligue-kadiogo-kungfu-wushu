from django.contrib import admin
from .models import (
    AnneeSportive, Rubrique, RubriqueGrade,
    TarifExamen, SessionExamen, AffectationJury, Inscription
)


@admin.register(AnneeSportive)
class AnneeSportiveAdmin(admin.ModelAdmin):
    list_display  = ('libelle', 'ligue', 'date_debut', 'date_fin', 'statut')
    list_filter   = ('statut', 'ligue')
    search_fields = ('libelle', 'ligue__nom_ligue')


@admin.register(Rubrique)
class RubriqueAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'actif')
    list_filter   = ('actif',)
    search_fields = ('nom',)


@admin.register(RubriqueGrade)
class RubriqueGradeAdmin(admin.ModelAdmin):
    list_display  = ('rubrique', 'grade', 'coefficient', 'note_minimale', 'actif')
    list_filter   = ('actif', 'grade')
    ordering      = ('grade__ordre', 'rubrique__nom')


@admin.register(TarifExamen)
class TarifExamenAdmin(admin.ModelAdmin):
    list_display  = ('grade', 'annee_sportive', 'montant')
    list_filter   = ('annee_sportive', 'grade')
    ordering      = ('annee_sportive', 'grade__ordre')


class AffectationJuryInline(admin.TabularInline):
    model  = AffectationJury
    extra  = 1
    fields = ('jury', 'date_affectation')
    readonly_fields = ('date_affectation',)


class InscriptionInline(admin.TabularInline):
    model   = Inscription
    extra   = 0
    fields  = ('pratiquant', 'grade_vise', 'montant', 'statut')
    readonly_fields = ('montant',)


@admin.register(SessionExamen)
class SessionExamenAdmin(admin.ModelAdmin):
    list_display  = (
        'titre', 'annee_sportive', 'date_examen', 'lieu', 'statut'
    )
    list_filter   = ('statut', 'annee_sportive')
    search_fields = ('titre', 'lieu')
    inlines       = [AffectationJuryInline, InscriptionInline]
    fieldsets     = (
        ('Informations générales', {
            'fields': ('annee_sportive', 'titre', 'date_examen', 'lieu')
        }),
        ('Inscriptions', {
            'fields': (
                'date_ouverture_inscriptions',
                'date_cloture_inscriptions'
            )
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
    )


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display  = ('pratiquant', 'session', 'grade_vise', 'montant', 'statut')
    list_filter   = ('statut', 'grade_vise', 'session')
    search_fields = ('pratiquant__nom', 'pratiquant__prenom')
    readonly_fields = ('montant', 'date_inscription')
