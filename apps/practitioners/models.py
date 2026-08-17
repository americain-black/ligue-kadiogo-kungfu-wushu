# pyrefly: ignore [missing-import]
from django.db import models


class Grade(models.Model):
    """
    Grade configurable par ligue.
    Ex : BLANC, ROUGE, ROUGE I, ROUGE II, ROUGE III…
    L'ordre hiérarchique est déterminé par id_grade (auto-incrémenté).
    """

    ligue    = models.ForeignKey(
        'ligues.Ligue',
        on_delete=models.CASCADE,
        related_name='grades',
        null=True, blank=True
    )
    nom      = models.CharField(max_length=50)
    id_grade = models.PositiveSmallIntegerField(
        default=0,
        help_text="Identifiant séquentiel du grade (auto-incrémenté à la création)"
    )
    actif    = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Grade'
        verbose_name_plural = 'Grades'
        ordering            = ['id_grade']

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.pk and self.id_grade == 0:
            # pyrefly: ignore [missing-import]
            from django.db.models import Max
            max_id = Grade.objects.filter(ligue=self.ligue).aggregate(m=Max('id_grade'))['m'] or 0
            self.id_grade = max_id + 1
        super().save(*args, **kwargs)


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
        on_delete=models.SET_NULL,
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
    bulletin_grade    = models.FileField(
        upload_to='bulletins_grade/',
        null=True, blank=True,
        verbose_name="Bulletin / attestation de grade",
        help_text="Requis si le grade actuel est ≥ 2ème grade"
    )
    actif             = models.BooleanField(default=True)
    date_inscription  = models.DateField(auto_now_add=True)
    matricule         = models.CharField(
        max_length=20, unique=True, null=True, blank=True,
        help_text="Attribué automatiquement lors de l'autorisation"
    )

    class Meta:
        verbose_name        = 'Licencié'
        verbose_name_plural = 'Licenciés'
        ordering            = ['grade_actuel__id_grade', 'nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom} — {self.club.nom_club}"

    def get_grade_display(self):
        return self.grade_actuel.nom if self.grade_actuel else "Sans grade"


class HistoriquePassageGrade(models.Model):
    """
    Rappel des moyennes/passages de grade antérieurs d'un licencié
    (saisis manuellement par la Ligue pour l'historique antérieur).
    """

    pratiquant = models.ForeignKey(
        Pratiquant,
        on_delete=models.CASCADE,
        related_name='historique_passages'
    )
    date_passage = models.DateField(
        null=True, blank=True,
        verbose_name="Date du passage",
        help_text="Date à laquelle le passage de grade a eu lieu"
    )
    grade_libelle = models.CharField(
        max_length=100,
        verbose_name="Grade",
        help_text="Grade visé ou obtenu (ex : JAUNE, BLEUE, ROUGE...)"
    )
    moyenne = models.DecimalField(
        max_digits=4, decimal_places=2,
        verbose_name="Moyenne sur 20"
    )
    rang = models.CharField(
        max_length=30, blank=True, default="—",
        verbose_name="Rang",
        help_text="Ex : 1er, 3 Ex, 5è..."
    )
    mention = models.CharField(
        max_length=50, blank=True, default="—",
        verbose_name="Mention",
        help_text="Ex : Bien, Passable, Assez-bien..."
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historique de passage de grade"
        verbose_name_plural = "Historiques de passage de grade"
        ordering = ['-date_passage', '-date_ajout']

    def __str__(self):
        return f"{self.pratiquant} — {self.grade_libelle} : {self.moyenne}/20"

