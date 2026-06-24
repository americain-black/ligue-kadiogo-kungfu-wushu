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
    jury          = models.ForeignKey(
        'accounts.Utilisateur',
        on_delete=models.PROTECT,
        related_name='notes_saisies'
    )
    note          = models.DecimalField(
        max_digits=4, decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(20)
        ],
        help_text="Note sur 20"
    )
    validee       = models.BooleanField(
        default=False,
        help_text="Une note validée ne peut plus être modifiée"
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
            f"{self.note}/20"
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
        self.validee        = True
        self.date_validation = timezone.now()
        self.save()
