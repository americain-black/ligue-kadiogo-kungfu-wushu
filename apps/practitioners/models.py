from django.db import models


class Grade(models.Model):
    """
    Grade configurable par ligue.
    Ex : Blanc, Jaune, Verte, Bleue, Marron, Noir.
    L'ordre permet de savoir quel grade est supérieur à un autre.
    Chaque ligue gère sa propre liste de grades.
    """

    ligue = models.ForeignKey(
        'ligues.Ligue',
        on_delete=models.CASCADE,
        related_name='grades',
        null=True, blank=True
    )
    nom   = models.CharField(max_length=50)
    ordre = models.PositiveSmallIntegerField(
        help_text="Ordre croissant : 1 = plus bas, 6 = plus haut"
    )
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Grade'
        verbose_name_plural = 'Grades'
        ordering            = ['ordre']

    def __str__(self):
        return self.nom


class Pratiquant(models.Model):
    """
    Pratiquant rattaché à un club.
    Son grade actuel évolue au fil des examens réussis.
    """

    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    club              = models.ForeignKey(
        'clubs.Club',
        on_delete=models.PROTECT,
        related_name='pratiquants'
    )
    grade_actuel      = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        related_name='pratiquants',
        null=True, blank=True
    )

    nom               = models.CharField(max_length=100)
    prenom            = models.CharField(max_length=100)
    date_naissance    = models.DateField()
    sexe              = models.CharField(max_length=1, choices=SEXE_CHOICES)
    lieu_naissance    = models.CharField(max_length=100, blank=True)
    telephone         = models.CharField(max_length=20, blank=True)
    photo             = models.ImageField(
        upload_to='pratiquants/',
        null=True, blank=True
    )
    actif             = models.BooleanField(default=True)
    date_inscription  = models.DateField(auto_now_add=True)
    matricule         = models.CharField(
        max_length=20, unique=True, null=True, blank=True,
        help_text="Attribué automatiquement lors de l'autorisation"
    )

    class Meta:
        verbose_name        = 'Pratiquant'
        verbose_name_plural = 'Pratiquants'
        ordering            = ['nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom} — {self.club.nom_club}"

    def get_grade_display(self):
        return self.grade_actuel.nom if self.grade_actuel else "Sans grade"
