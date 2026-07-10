from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class NoteRubrique(models.Model):
    """
    Note saisie par un membre du jury pour un candidat
    sur une rubrique précise.
    La moyenne pondérée est calculée automatiquement.
    """

    inscription   = models.ForeignKey(
        'exams.Inscription',
        on_delete=models.CASCADE,
        related_name='notes'
    )
    rubrique_grade = models.ForeignKey(
        'exams.RubriqueGrade',
        on_delete=models.PROTECT,
        related_name='notes'
    )
    affectation   = models.ForeignKey(
        'exams.AffectationJury',
        on_delete=models.PROTECT,
        related_name='notes'
    )
    note          = models.DecimalField(
        max_digits=4, decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ],
        help_text="Note sur 5"
    )
    validee       = models.BooleanField(
        default=False,
        help_text="Une note validée ne peut plus être modifiée"
    )
    correction_demandee = models.BooleanField(
        default=False,
        help_text="Le jury a demandé une autorisation de correction au Gestionnaire Ligue"
    )
    date_saisie   = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Note par rubrique'
        verbose_name_plural = 'Notes par rubrique'
        unique_together     = ('inscription', 'rubrique_grade')
        ordering            = ['inscription', 'rubrique_grade__rubrique__nom']

    def __str__(self):
        return (
            f"{self.inscription.pratiquant} — "
            f"{self.rubrique_grade.rubrique.nom} : "
            f"{self.note}/5"
        )

    def clean(self):
        if self.validee and self.pk:
            ancienne = NoteRubrique.objects.get(pk=self.pk)
            if ancienne.validee:
                raise ValidationError(
                    "Cette note est validée et ne peut plus être modifiée."
                )

    def valider(self):
        from django.utils import timezone
        self.validee             = True
        self.correction_demandee = False
        self.date_validation     = timezone.now()
        self.save()

    def demander_correction(self):
        """Appelée par le jury pour signaler une erreur sur une note déjà validée."""
        if not self.validee:
            raise ValidationError("Cette note n'est pas encore validée.")
        self.correction_demandee = True
        self.save()

    def deverrouiller(self):
        """Appelée par le Gestionnaire Ligue pour autoriser la correction d'une note."""
        if not self.validee:
            raise ValidationError("Cette note n'est pas validée.")
        self.validee             = False
        self.correction_demandee = False
        self.date_validation     = None
        self.save()
