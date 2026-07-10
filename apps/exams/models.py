from django.db import models
from django.db.models import F
from django.core.exceptions import ValidationError


class AnneeSportive(models.Model):

    STATUT_CHOICES = [
        ('ACTIVE',   'Active'),
        ('CLOTUREE', 'Clôturée'),
    ]

    ligue      = models.ForeignKey(
        'ligues.Ligue',
        on_delete=models.PROTECT,
        related_name='annees_sportives'
    )
    libelle    = models.CharField(
        max_length=20,
        help_text="Ex : 2025-2026"
    )
    date_debut = models.DateField()
    date_fin   = models.DateField()
    statut     = models.CharField(
        max_length=10,
        choices=STATUT_CHOICES,
        default='ACTIVE'
    )

    class Meta:
        verbose_name        = 'Année sportive'
        verbose_name_plural = 'Années sportives'
        ordering            = ['-date_debut']
        unique_together     = ('ligue', 'libelle')

    def __str__(self):
        return f"{self.libelle} — {self.ligue.sigle}"

    def est_active(self):
        return self.statut == 'ACTIVE'


class Rubrique(models.Model):
    """
    Épreuve d'un examen.
    Ex : Kata, Combat Sanda, Théorie, Condition physique...
    Configurable dans le système.
    """

    nom         = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    actif       = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Rubrique'
        verbose_name_plural = 'Rubriques'
        ordering            = ['nom']

    def __str__(self):
        return self.nom


class RubriqueGrade(models.Model):
    """
    Associe une rubrique à un grade avec son coefficient
    et la note minimale requise pour valider cette épreuve.
    Ex : Kata — grade Bleue — coeff 3 — note min 3/5
    """

    rubrique      = models.ForeignKey(
        Rubrique,
        on_delete=models.PROTECT,
        related_name='rubrique_grades'
    )
    grade         = models.ForeignKey(
        'practitioners.Grade',
        on_delete=models.CASCADE,
        related_name='rubrique_grades'
    )
    coefficient   = models.PositiveSmallIntegerField(default=1)
    note_minimale = models.DecimalField(
        max_digits=4, decimal_places=2, default=3,
        help_text="Note minimale sur 5 pour valider cette épreuve"
    )
    actif         = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Rubrique par grade'
        verbose_name_plural = 'Rubriques par grade'
        unique_together     = ('rubrique', 'grade')
        ordering            = ['grade__id_grade', 'rubrique__nom']

    def __str__(self):
        return (
            f"{self.rubrique.nom} — {self.grade.nom} "
            f"(coeff {self.coefficient})"
        )


class OptionExamen(models.Model):
    """
    Option/style de pratique proposé lors des examens.
    Ex : Shaolin, Wu Dang, Sanda…
    Géré dynamiquement par la ligue.
    """

    ligue = models.ForeignKey(
        'ligues.Ligue',
        on_delete=models.CASCADE,
        related_name='options_examen'
    )
    nom   = models.CharField(max_length=100)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Option d'examen"
        verbose_name_plural = "Options d'examen"
        unique_together     = ('ligue', 'nom')
        ordering            = ['nom']

    def __str__(self):
        return self.nom


class ParametresExamen(models.Model):
    """
    Paramètres financiers d'examen pour une ligue.
    Le GC collecte les droits auprès de ses pratiquants puis reverse
    un pourcentage défini ici à la ligue.
    """

    ligue = models.OneToOneField(
        'ligues.Ligue',
        on_delete=models.CASCADE,
        related_name='parametres_examen'
    )
    pourcentage_ligue = models.DecimalField(
        max_digits=5, decimal_places=2, default=25,
        help_text="Pourcentage des droits d'examen reversé à la ligue (ex : 25 → le GC paie 25 % du total)"
    )

    class Meta:
        verbose_name        = "Paramètres d'examen"
        verbose_name_plural = "Paramètres d'examen"

    def __str__(self):
        return f"Paramètres examen — {self.ligue.sigle} ({self.pourcentage_ligue} % à la ligue)"

    @property
    def pourcentage_club(self):
        return 100 - self.pourcentage_ligue


class ModeleMatricule(models.Model):
    """
    Modèle de génération des matricules pour une ligue.
    Format : {prefixe}{2 derniers chiffres de l'année}{séquence 4 chiffres}
    Ex : LK260026  →  préfixe=LK, année=2026, séquence=26
    Un seul modèle par ligue.
    """

    ligue             = models.OneToOneField(
        'ligues.Ligue',
        on_delete=models.CASCADE,
        related_name='modele_matricule'
    )
    prefixe           = models.CharField(
        max_length=10,
        help_text="Sigle de la ligue, ex : LK"
    )
    derniere_sequence = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name        = 'Modèle de matricule'
        verbose_name_plural = 'Modèles de matricule'

    def __str__(self):
        return f"Modèle {self.prefixe} — ligue {self.ligue.sigle}"

    def generer(self, annee):
        """Incrémente la séquence et retourne le matricule généré."""
        self.derniere_sequence += 1
        self.save(update_fields=['derniere_sequence'])
        return f"{self.prefixe}{str(annee)[-2:]}{self.derniere_sequence:04d}"


class TarifExamen(models.Model):
    """
    Tarif des droits d'examen par grade et par année sportive.
    Configurable chaque année par la ligue.
    Ex : passer en Bleue en 2025-2026 = 5 000 FCFA
    """

    annee_sportive = models.ForeignKey(
        AnneeSportive,
        on_delete=models.PROTECT,
        related_name='tarifs'
    )
    grade          = models.ForeignKey(
        'practitioners.Grade',
        on_delete=models.CASCADE,
        related_name='tarifs'
    )
    montant        = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Montant en FCFA"
    )

    class Meta:
        verbose_name        = "Tarif d'examen"
        verbose_name_plural = "Tarifs d'examen"
        unique_together     = ('annee_sportive', 'grade')
        ordering            = ['annee_sportive', 'grade__id_grade']

    def __str__(self):
        return (
            f"{self.grade.nom} — {self.annee_sportive.libelle} : "
            f"{self.montant} FCFA"
        )


class SessionExamen(models.Model):
    """
    Session d'examen organisée par la ligue.
    Une session peut accueillir des candidats de plusieurs grades.
    """

    STATUT_CHOICES = [
        ('EN_PREPARATION',         'En préparation'),
        ('INSCRIPTIONS_OUVERTES',  'Inscriptions ouvertes'),
        ('INSCRIPTIONS_CLOSES',    'Inscriptions closes'),
        ('EN_COURS',               'En cours'),
        ('CLOTUREE',               'Clôturée'),
        ('RESULTATS_PUBLIES',      'Résultats publiés'),
    ]

    annee_sportive              = models.ForeignKey(
        AnneeSportive,
        on_delete=models.PROTECT,
        related_name='sessions'
    )
    titre                       = models.CharField(
        max_length=200,
        help_text="Ex : Examen Mai 2026"
    )
    date_examen                 = models.DateField()
    lieu                        = models.CharField(max_length=200)
    date_ouverture_inscriptions = models.DateField()
    date_cloture_inscriptions   = models.DateField()
    date_limite_paiement        = models.DateField(
        null=True, blank=True,
        help_text="Date limite pour compléter ou régulariser le paiement des droits d'examen"
    )
    statut                      = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='EN_PREPARATION'
    )

    class Meta:
        verbose_name        = "Session d'examen"
        verbose_name_plural = "Sessions d'examen"
        ordering            = ['-date_examen']

    def __str__(self):
        return f"{self.titre} ({self.date_examen})"

    # ── Méthodes de workflow ──────────────────────────────────────────

    def ouvrir_inscriptions(self):
        if self.statut != 'EN_PREPARATION':
            raise ValidationError("La session n'est pas en préparation.")
        self.statut = 'INSCRIPTIONS_OUVERTES'
        self.save()

    def cloturer_inscriptions(self):
        if self.statut != 'INSCRIPTIONS_OUVERTES':
            raise ValidationError("Les inscriptions ne sont pas ouvertes.")
        self.statut = 'INSCRIPTIONS_CLOSES'
        self.save()

    def cloturer_session(self):
        if self.statut != 'EN_COURS':
            raise ValidationError("La session n'est pas en cours.")
        self.statut = 'CLOTUREE'
        self.save()

    def publier_resultats(self):
        if self.statut != 'CLOTUREE':
            raise ValidationError("La session n'est pas clôturée.")
        self.statut = 'RESULTATS_PUBLIES'
        self.save()


class AffectationJury(models.Model):
    """
    Affectation d'un membre du jury à une session d'examen.
    Un jury peut évaluer plusieurs grades, options et rubriques.
    """

    session          = models.ForeignKey(
        SessionExamen,
        on_delete=models.CASCADE,
        related_name='affectations_jury'
    )
    jury             = models.ForeignKey(
        'accounts.Utilisateur',
        on_delete=models.PROTECT,
        related_name='affectations_jury'
    )
    grades    = models.ManyToManyField(
        'practitioners.Grade',
        blank=True,
        related_name='affectations_jury',
        verbose_name='Grades à évaluer'
    )
    options   = models.ManyToManyField(
        OptionExamen,
        blank=True,
        related_name='affectations_jury',
        verbose_name='Options à évaluer'
    )
    rubriques = models.ManyToManyField(
        Rubrique,
        blank=True,
        related_name='affectations_jury',
        verbose_name='Rubriques à évaluer'
    )
    date_affectation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Affectation jury'
        verbose_name_plural = 'Affectations jury'
        unique_together     = ('session', 'jury')

    def __str__(self):
        return f"{self.jury} — {self.session}"


class Inscription(models.Model):
    """
    Inscription d'un pratiquant à une session d'examen.
    Le montant est calculé automatiquement depuis TarifExamen.
    """

    STATUT_CHOICES = [
        ('EN_ATTENTE_PAIEMENT', 'En attente de paiement'),
        ('PAIEMENT_VALIDE',     'Paiement validé'),
        ('AUTORISE',            'Autorisé à participer'),
        ('EXCLU',               'Exclu'),
    ]

    session     = models.ForeignKey(
        SessionExamen,
        on_delete=models.PROTECT,
        related_name='inscriptions'
    )
    pratiquant  = models.ForeignKey(
        'practitioners.Pratiquant',
        on_delete=models.CASCADE,
        related_name='inscriptions'
    )
    grade_vise  = models.ForeignKey(
        'practitioners.Grade',
        on_delete=models.PROTECT,
        related_name='inscriptions'
    )
    option      = models.ForeignKey(
        OptionExamen,
        on_delete=models.PROTECT,
        related_name='inscriptions'
    )
    montant     = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Calculé automatiquement depuis le tarif du grade visé"
    )
    statut      = models.CharField(
        max_length=25,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE_PAIEMENT'
    )
    motif_exclusion  = models.TextField(
        blank=True,
        verbose_name="Motif d'exclusion",
        help_text="Raison de l'exclusion communiquée au club"
    )
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Inscription'
        verbose_name_plural = 'Inscriptions'
        unique_together     = ('session', 'pratiquant')
        ordering            = ['pratiquant__nom']

    def __str__(self):
        return (
            f"{self.pratiquant} — {self.session.titre} "
            f"(vise : {self.grade_vise})"
        )

    def save(self, *args, **kwargs):
        # Calcule automatiquement le montant depuis TarifExamen
        if not self.montant or self.montant == 0:
            try:
                tarif = TarifExamen.objects.get(
                    annee_sportive=self.session.annee_sportive,
                    grade=self.grade_vise
                )
                self.montant = tarif.montant
            except TarifExamen.DoesNotExist:
                pass
        super().save(*args, **kwargs)
