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

    # Champs de sécurité et d'authentification
    code_verification = models.CharField(
        max_length=64, unique=True, null=True, blank=True,
        help_text="Code unique d'authentification du bulletin"
    )
    hash_securite     = models.CharField(
        max_length=64, blank=True,
        help_text="Empreinte cryptographique SHA-256 de sécurité"
    )
    date_emission     = models.DateTimeField(null=True, blank=True)

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
        self.get_or_create_code_securite()
        self.save()

        # Si admis, met à jour le grade du pratiquant
        if self.decision == 'ADMIS':
            pratiquant             = self.inscription.pratiquant
            pratiquant.grade_actuel = self.inscription.grade_vise
            pratiquant.save()

    def get_or_create_code_securite(self):
        """
        Génère ou récupère un code d'authentification unique et son hash SHA-256.
        Format du code: LK-BUL-<SESSION_ANNEE>-<RANDOM_HEX>
        Exemple: LK-BUL-2026-F8A3B291
        """
        import uuid
        import hashlib
        from django.conf import settings
        from django.utils import timezone

        if not self.code_verification:
            annee = self.inscription.session.date_examen.year if (self.inscription and self.inscription.session and self.inscription.session.date_examen) else timezone.now().year
            prefixe = "LK-BUL"
            if self.inscription and self.inscription.session and self.inscription.session.annee_sportive and self.inscription.session.annee_sportive.ligue:
                prefixe = self.inscription.session.annee_sportive.ligue.get_bulletin_prefixe_securite()

            rand_code = uuid.uuid4().hex[:8].upper()
            code = f"{prefixe}-{annee}-{rand_code}"
            
            raw_data = f"{code}:{self.pk}:{self.inscription.pratiquant.matricule if self.inscription else ''}:{self.moyenne}:{settings.SECRET_KEY}"
            hash_val = hashlib.sha256(raw_data.encode('utf-8')).hexdigest()
            
            self.code_verification = code
            self.hash_securite = hash_val
            if not self.date_emission:
                self.date_emission = timezone.now()
            self.save(update_fields=['code_verification', 'hash_securite', 'date_emission'])
        return self.code_verification

