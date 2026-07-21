from django.db import models


class Resultat(models.Model):
    """
    Résultat final d'un candidat après compilation de toutes ses notes.
    Calculé automatiquement depuis les NoteRubrique.
    Mis à jour le grade du pratiquant si ADMIS.
    """

    DECISION_CHOICES = [
        ('ADMIS',    'Admis'),
        ('AJOURNÉ', 'Ajourné'),
    ]

    inscription    = models.OneToOneField(
        'exams.Inscription',
        on_delete=models.CASCADE,
        related_name='resultat'
    )
    moyenne        = models.DecimalField(
        max_digits=4, decimal_places=2,
        help_text="Moyenne pondérée calculée automatiquement, sur 20"
    )
    decision       = models.CharField(
        max_length=10,
        choices=DECISION_CHOICES
    )
    publie         = models.BooleanField(
        default=False,
        help_text="Résultat visible par le club et le public"
    )
    bulletin_pdf   = models.FileField(
        upload_to='bulletins/',
        null=True, blank=True,
        help_text="Bulletin PDF généré automatiquement"
    )
    date_calcul    = models.DateTimeField(auto_now_add=True)
    date_publication = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Résultat'
        verbose_name_plural = 'Résultats'
        ordering            = ['inscription__pratiquant__nom']

    def __str__(self):
        return (
            f"{self.inscription.pratiquant} — "
            f"{self.inscription.session.titre} : "
            f"{self.moyenne}/20 ({self.get_decision_display()})"
        )

    @classmethod
    def calculer(cls, inscription):
        """
        Calcule la moyenne pondérée d'un candidat sur 20
        à partir de ses notes (sur 5) et crée/met à jour le Résultat.
        """
        from apps.evaluations.models import NoteRubrique

        notes = NoteRubrique.objects.filter(
            inscription=inscription,
            validee=True
        )

        if not notes.exists():
            return None

        total_points = sum(n.note * n.rubrique_grade.coefficient for n in notes)
        total_coeffs = sum(n.rubrique_grade.coefficient for n in notes)
        # Les notes sont sur 5 : on ramène la moyenne pondérée sur 20.
        moyenne = (total_points / total_coeffs * 4) if total_coeffs else 0

        decision = 'ADMIS' if moyenne >= 10 else 'AJOURNÉ'

        resultat, _ = cls.objects.update_or_create(
            inscription=inscription,
            defaults={
                'moyenne' : round(moyenne, 2),
                'decision': decision,
            }
        )
        return resultat

    def rang(self):
        """
        Position du candidat parmi les ADMIS de son groupe (même session,
        même grade visé, même option). Classement par moyenne décroissante ;
        les ex-aequo partagent le même rang.
        Retourne (rang, total) ou (None, None) si le résultat n'est pas ADMIS.
        """
        if self.decision != 'ADMIS':
            return None, None

        inscription = self.inscription
        admis = Resultat.objects.filter(
            decision='ADMIS',
            inscription__session_id=inscription.session_id,
            inscription__grade_vise_id=inscription.grade_vise_id,
            inscription__option_id=inscription.option_id,
        )
        total = admis.count()
        mieux_classes = admis.filter(moyenne__gt=self.moyenne).count()
        return mieux_classes + 1, total

    def mention(self):
        """Mention littérale correspondant à la moyenne sur 20."""
        m = self.moyenne
        if m < 10:
            return 'Insuffisante'
        if m < 12:
            return 'Passable'
        if m < 14:
            return 'Assez-bien'
        if m < 16:
            return 'Bien'
        return 'Très bien'

    def publier(self):
        from django.utils import timezone
        self.publie           = True
        self.date_publication = timezone.now()
        self.save()

        # Si admis, met à jour le grade du pratiquant
        if self.decision == 'ADMIS':
            pratiquant             = self.inscription.pratiquant
            pratiquant.grade_actuel = self.inscription.grade_vise
            pratiquant.save()
