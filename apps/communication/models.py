from django.db import models


class Actualite(models.Model):
    """
    Actualité publiée par la ligue ou soumise par un club.
    Les actualités des clubs doivent être validées par la ligue
    avant d'être rendues publiques.
    """

    STATUT_CHOICES = [
        ('BROUILLON',   'Brouillon'),
        ('EN_ATTENTE',  'En attente de validation'),
        ('PUBLIEE',     'Publiée'),
        ('REJETEE',     'Rejetée'),
    ]

    SOURCE_CHOICES = [
        ('LIGUE', 'Ligue'),
        ('CLUB',  'Club'),
    ]

    ligue          = models.ForeignKey(
        'ligues.Ligue',
        on_delete=models.CASCADE,
        related_name='actualites'
    )
    club           = models.ForeignKey(
        'clubs.Club',
        on_delete=models.CASCADE,
        related_name='actualites',
        null=True, blank=True,
        help_text="Renseigné uniquement si l'actualité vient d'un club"
    )
    auteur         = models.ForeignKey(
        'accounts.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='actualites_redigees'
    )
    source         = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    titre          = models.CharField(max_length=200)
    contenu        = models.TextField()
    image          = models.ImageField(
        upload_to='actualites/',
        null=True, blank=True
    )
    statut         = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='BROUILLON'
    )
    motif_rejet    = models.TextField(blank=True)
    date_creation  = models.DateTimeField(auto_now_add=True)
    date_publication = models.DateTimeField(null=True, blank=True)
    validee_par    = models.ForeignKey(
        'accounts.Utilisateur',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='actualites_validees'
    )

    class Meta:
        verbose_name        = 'Actualité'
        verbose_name_plural = 'Actualités'
        ordering            = ['-date_creation']

    def __str__(self):
        return f"{self.titre} ({self.get_statut_display()})"

    def soumettre(self):
        self.statut = 'EN_ATTENTE'
        self.save()

    def publier(self, validee_par=None):
        from django.utils import timezone
        self.statut           = 'PUBLIEE'
        self.validee_par      = validee_par
        self.date_publication = timezone.now()
        self.save()

    def rejeter(self, motif=''):
        self.statut      = 'REJETEE'
        self.motif_rejet = motif
        self.save()


class Document(models.Model):
    """
    Document officiel publié par la ligue.
    Peut être public (visible par tous) ou privé (clubs affiliés uniquement).
    """

    TYPE_CHOICES = [
        ('REGLEMENT',  'Règlement'),
        ('FORMULAIRE', 'Formulaire'),
        ('CIRCULAIRE', 'Circulaire'),
        ('AUTRE',      'Autre'),
    ]

    ligue          = models.ForeignKey(
        'ligues.Ligue',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    auteur         = models.ForeignKey(
        'accounts.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_publies'
    )
    titre          = models.CharField(max_length=200)
    type_document  = models.CharField(
        max_length=15,
        choices=TYPE_CHOICES,
        default='AUTRE'
    )
    fichier        = models.FileField(upload_to='documents/')
    est_public     = models.BooleanField(
        default=True,
        help_text="Public = visible par tous. Privé = clubs affiliés uniquement."
    )
    date_publication = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Document'
        verbose_name_plural = 'Documents'
        ordering            = ['-date_publication']

    def __str__(self):
        return f"{self.titre} ({self.get_type_document_display()})"
