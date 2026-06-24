from django.db import models
from django.core.exceptions import ValidationError


def chemin_preuve_affiliation(instance, filename):
    return (
        f"preuves_paiement/affiliation/"
        f"club_{instance.demande.club.id}/"
        f"{filename}"
    )


def chemin_preuve_examen(instance, filename):
    return (
        f"preuves_paiement/examen/"
        f"club_{instance.club.id}/"
        f"session_{instance.session.id}/"
        f"{filename}"
    )


class PaiementAffiliation(models.Model):
    """
    Preuve de paiement des frais d'affiliation soumise par un club.
    Une preuve par demande d'affiliation.
    """

    STATUT_CHOICES = [
        ('EN_ATTENTE',  'En attente de vérification'),
        ('VALIDE',      'Validé'),
        ('REJETE',      'Rejeté'),
    ]

    demande        = models.OneToOneField(
        'clubs.DemandeAffiliation',
        on_delete=models.CASCADE,
        related_name='paiement'
    )
    montant_paye   = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Montant indiqué sur la preuve de paiement"
    )
    reference      = models.CharField(
        max_length=100, blank=True,
        help_text="Numéro de reçu ou référence de la transaction"
    )
    fichier_preuve = models.FileField(
        upload_to=chemin_preuve_affiliation,
        help_text="Reçu de paiement (PDF, JPG, PNG)"
    )
    statut         = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE'
    )
    motif_rejet    = models.TextField(blank=True)
    date_soumission = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    valide_par      = models.ForeignKey(
        'accounts.Utilisateur',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='paiements_affiliation_valides'
    )

    class Meta:
        verbose_name        = "Paiement d'affiliation"
        verbose_name_plural = "Paiements d'affiliation"
        ordering            = ['-date_soumission']

    def __str__(self):
        return (
            f"Paiement affiliation — {self.demande.club.nom_club} "
            f"({self.get_statut_display()})"
        )

    def valider(self, gestionnaire):
        from django.utils import timezone
        self.statut          = 'VALIDE'
        self.valide_par      = gestionnaire
        self.date_validation = timezone.now()
        self.save()
        # Fait avancer la demande d'affiliation
        self.demande.valider_par_financier()

    def rejeter(self, gestionnaire, motif=''):
        self.statut       = 'REJETE'
        self.valide_par   = gestionnaire
        self.motif_rejet  = motif
        self.save()
        # Remet la demande en attente de paiement
        self.demande.rejeter_par_financier(motif=motif)


class PaiementExamen(models.Model):
    """
    Preuve de paiement global des droits d'examen soumise par un club.
    Une seule preuve couvre tous les pratiquants du club pour une session.
    """

    STATUT_CHOICES = [
        ('EN_ATTENTE',  'En attente de vérification'),
        ('VALIDE',      'Validé'),
        ('REJETE',      'Rejeté'),
    ]

    club           = models.ForeignKey(
        'clubs.Club',
        on_delete=models.PROTECT,
        related_name='paiements_examen'
    )
    session        = models.ForeignKey(
        'exams.SessionExamen',
        on_delete=models.PROTECT,
        related_name='paiements'
    )
    montant_paye   = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Montant total payé pour tous les pratiquants"
    )
    montant_attendu = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Calculé automatiquement (somme des tarifs des inscrits)"
    )
    reference      = models.CharField(
        max_length=100, blank=True,
        help_text="Numéro de reçu ou référence de la transaction"
    )
    fichier_preuve = models.FileField(
        upload_to=chemin_preuve_examen,
        help_text="Reçu de paiement (PDF, JPG, PNG)"
    )
    statut         = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE'
    )
    motif_rejet    = models.TextField(blank=True)
    date_soumission = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    valide_par      = models.ForeignKey(
        'accounts.Utilisateur',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='paiements_examen_valides'
    )

    class Meta:
        verbose_name        = "Paiement d'examen"
        verbose_name_plural = "Paiements d'examen"
        unique_together     = ('club', 'session')
        ordering            = ['-date_soumission']

    def __str__(self):
        return (
            f"Paiement examen — {self.club.nom_club} "
            f"— {self.session.titre} ({self.get_statut_display()})"
        )

    def valider(self, gestionnaire):
        from django.utils import timezone
        from apps.exams.models import Inscription
        self.statut          = 'VALIDE'
        self.valide_par      = gestionnaire
        self.date_validation = timezone.now()
        self.save()
        # Met à jour le statut de toutes les inscriptions du club
        Inscription.objects.filter(
            session=self.session,
            pratiquant__club=self.club
        ).update(statut='PAIEMENT_VALIDE')

    def rejeter(self, gestionnaire, motif=''):
        self.statut      = 'REJETE'
        self.valide_par  = gestionnaire
        self.motif_rejet = motif
        self.save()
