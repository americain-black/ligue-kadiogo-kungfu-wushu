# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.core.exceptions import ValidationError


class Club(models.Model):

    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('AFFILIE',    'Affilié'),
        ('SUSPENDU',   'Suspendu'),
        ('REJETE',     'Rejeté'),
    ]

    ligue = models.ForeignKey(
        'ligues.Ligue',
        on_delete=models.PROTECT,
        related_name='clubs'
    )
    utilisateur = models.OneToOneField(
        'accounts.Utilisateur',
        on_delete=models.PROTECT,
        related_name='club',
        null=True, blank=True
    )

    nom_club   = models.CharField(max_length=200)
    sigle_club = models.CharField(max_length=20,  blank=True)
    nom_fondateur = models.CharField(max_length=200, blank=True, verbose_name="Maître / Fondateur du club", help_text="Nom du Maître principal / Fondateur du club")
    code_club  = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Code unique du club",
        help_text="Généré automatiquement (ex : CL01, CL02...) si laissé vide."
    )
    localite   = models.CharField(max_length=100)
    adresse    = models.CharField(max_length=200, blank=True)
    telephone  = models.CharField(max_length=20,  blank=True)
    email      = models.EmailField(blank=True)
    description = models.TextField(blank=True, verbose_name="Description / Présentation du club", help_text="Présentation courte du club pour l'annuaire public")
    latitude   = models.FloatField(null=True, blank=True, verbose_name="Latitude", help_text="Coordonnée latitude (ex: 12.3714)")
    longitude  = models.FloatField(null=True, blank=True, verbose_name="Longitude", help_text="Coordonnée longitude (ex: -1.5197)")
    statut_club = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE'
    )
    date_creation = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Club'
        verbose_name_plural = 'Clubs'
        ordering            = ['nom_club']

    def __str__(self):
        return f"{self.nom_club} ({self.code_club or self.sigle_club or self.ligue.sigle})"

    def save(self, *args, **kwargs):
        if not self.code_club:
            # pyrefly: ignore [missing-import]
            from django.db.models import Q
            qs = Club.objects.all()
            if self.ligue_id:
                qs = qs.filter(ligue_id=self.ligue_id)
            count = qs.count() + 1
            proposed_code = f"CL{count:02d}"
            while qs.filter(code_club__iexact=proposed_code).exclude(pk=self.pk).exists():
                count += 1
                proposed_code = f"CL{count:02d}"
            self.code_club = proposed_code
        super().save(*args, **kwargs)

    def est_affilie(self):
        return self.statut_club == 'AFFILIE'


def chemin_piece_affiliation(instance, filename):
    """
    Chemin de stockage :
    pieces_affiliation/club_<id>/annee_<libelle>/<filename>
    """
    return (
        f"pieces_affiliation/"
        f"club_{instance.demande.club.id}/"
        f"annee_{instance.demande.annee_sportive.libelle}/"
        f"{filename}"
    )


class DemandeAffiliation(models.Model):

    STATUT_CHOICES = [
        ('EN_ATTENTE_PAIEMENT',        'En attente de paiement'),
        ('EN_ATTENTE_VALID_FINANCIER', 'En attente validation financier'),
        ('EN_ATTENTE_VALID_LIGUE',     'En attente validation ligue'),
        ('APPROUVEE',                  'Approuvée'),
        ('REJETEE',                    'Rejetée — modification possible'),
    ]

    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='demandes_affiliation'
    )
    annee_sportive = models.ForeignKey(
        'exams.AnneeSportive',
        on_delete=models.PROTECT,
        related_name='demandes_affiliation'
    )
    date_demande       = models.DateField(auto_now_add=True)
    date_modification  = models.DateTimeField(auto_now=True)
    montant_frais      = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    statut_affiliation = models.CharField(
        max_length=40,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE_PAIEMENT'
    )
    motif_rejet        = models.TextField(blank=True)
    nombre_soumissions = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name        = "Demande d'affiliation"
        verbose_name_plural = "Demandes d'affiliation"
        unique_together     = ('club', 'annee_sportive')
        ordering            = ['-date_demande']

    def __str__(self):
        return (
            f"{self.club.nom_club} — "
            f"{self.annee_sportive} "
            f"({self.get_statut_affiliation_display()})"
        )

    # ── Méthodes de workflow ──────────────────────────────────────────

    def peut_etre_modifiee(self):
        """
        Le club peut modifier sa demande uniquement
        si elle a été rejetée.
        """
        return self.statut_affiliation == 'REJETEE'

    def soumettre(self):
        """
        Première soumission ou re-soumission après rejet.
        Réinitialise le motif de rejet et incrémente le compteur.
        """
        if self.nombre_soumissions > 0 and not self.peut_etre_modifiee():
            raise ValidationError(
                "Cette demande ne peut pas être resoumise dans son état actuel."
            )
        self.statut_affiliation = 'EN_ATTENTE_PAIEMENT'
        self.motif_rejet        = ''
        self.nombre_soumissions += 1
        self.save()
        # Supprime les anciennes pièces justificatives
        # pour repartir sur une base propre
        self.pieces_justificatives.all().delete()

    def soumettre_preuve_paiement(self):
        """
        Appelée par le Gestionnaire Club après avoir payé et
        transmis la preuve de paiement.
        La demande passe en attente de validation par le financier.
        """
        if self.statut_affiliation != 'EN_ATTENTE_PAIEMENT':
            raise ValidationError(
                "La preuve de paiement ne peut être soumise "
                "que lorsque la demande est en attente de paiement."
            )
        self.statut_affiliation = 'EN_ATTENTE_VALID_FINANCIER'
        self.save()

    def valider_par_financier(self):
        """Appelée par le Gestionnaire Financier."""
        self.statut_affiliation = 'EN_ATTENTE_VALID_LIGUE'
        self.save()

    def rejeter_par_financier(self, motif=''):
        """
        Le financier rejette la preuve de paiement.
        Le club doit re-soumettre un paiement.
        """
        self.statut_affiliation = 'EN_ATTENTE_PAIEMENT'
        self.motif_rejet        = motif
        self.save()

    def approuver(self):
        """Appelée par le Gestionnaire Ligue."""
        self.statut_affiliation  = 'APPROUVEE'
        self.club.statut_club    = 'AFFILIE'
        self.club.save()
        self.save()

    def rejeter_par_ligue(self, motif=''):
        """
        La ligue rejette la demande.
        Le club pourra la modifier et resoumettre.
        """
        self.statut_affiliation = 'REJETEE'
        self.motif_rejet        = motif
        self.save()


class PieceJustificativeAffiliation(models.Model):
    """
    Fichiers joints à une demande d'affiliation.
    Plusieurs fichiers possibles par demande :
    statuts, récépissé, liste des membres, etc.
    """

    TYPE_CHOICES = [
        ('STATUTS',   'Statuts du club'),
        ('RECEPISSE', 'Récépissé officiel'),
        ('LISTE',     'Liste des membres fondateurs'),
        ('AUTRE',     'Autre document'),
    ]

    demande     = models.ForeignKey(
        DemandeAffiliation,
        on_delete=models.CASCADE,
        related_name='pieces_justificatives'
    )
    type_piece  = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='AUTRE'
    )
    fichier     = models.FileField(
        upload_to=chemin_piece_affiliation,
        help_text="Formats acceptés : PDF, JPG, PNG (max 5 Mo)"
    )
    nom_fichier = models.CharField(max_length=200, blank=True)
    date_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Pièce justificative'
        verbose_name_plural = 'Pièces justificatives'

    def __str__(self):
        return (
            f"{self.get_type_piece_display()} — "
            f"{self.demande.club.nom_club}"
        )

    def save(self, *args, **kwargs):
        if self.fichier and not self.nom_fichier:
            self.nom_fichier = self.fichier.name
        super().save(*args, **kwargs)


class ParametresAffiliation(models.Model):
    """
    Montant des frais d'affiliation pour une ligue.
    Défini par le Gestionnaire de Ligue, réutilisé pour
    chaque nouvelle demande d'affiliation de la saison.
    """

    ligue = models.OneToOneField(
        'ligues.Ligue',
        on_delete=models.CASCADE,
        related_name='parametres_affiliation'
    )
    montant_frais_affiliation = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Montant des frais d'affiliation dus par un club (FCFA)"
    )

    class Meta:
        verbose_name        = "Paramètres d'affiliation"
        verbose_name_plural = "Paramètres d'affiliation"

    def __str__(self):
        return f"Paramètres affiliation — {self.ligue.sigle} ({self.montant_frais_affiliation} FCFA)"


class VoletOrganigrammeClub(models.Model):
    club        = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='volets')
    nom_volet   = models.CharField(max_length=200)
    ordre       = models.PositiveIntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Volet organigramme club'
        verbose_name_plural = 'Volets organigramme club'
        ordering            = ['ordre', 'date_creation']

    def __str__(self):
        return f"{self.club.nom_club} — {self.nom_volet}"


class MembreOrganigrammeClub(models.Model):
    volet               = models.ForeignKey(VoletOrganigrammeClub, on_delete=models.CASCADE, related_name='membres')
    nom                 = models.CharField(max_length=100)
    prenom              = models.CharField(max_length=100)
    contact             = models.CharField(max_length=50, blank=True)
    fonction            = models.CharField(max_length=200)
    ordre               = models.PositiveIntegerField(default=1, verbose_name="Ligne / Rang hiérarchique", help_text="Numéro de ligne : 1 = Ligne du haut (Président), 2 = Ligne du dessous (VP), 3 = Ligne 3...")
    date_debut_fonction = models.DateField(null=True, blank=True)
    actif               = models.BooleanField(default=True)
    date_ajout          = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Membre organigramme club'
        verbose_name_plural = 'Membres organigramme club'
        ordering            = ['-actif', 'ordre', 'nom', 'prenom']

    def __str__(self):
        return f"[Ligne {self.ordre}] {self.prenom} {self.nom} — {self.fonction}"

    @property
    def sigle_seul(self):
        f = (self.fonction or '').strip()
        if not f:
            return ""
            
        f_lower = f.lower().replace('é', 'e').replace('è', 'e')
        
        SIGLES = [
            ('vice-president', 'VPT'),
            ('vice president', 'VPT'),
            ('vice-président', 'VPT'),
            ('vice président', 'VPT'),
            ('president', 'PDT'),
            ('président', 'PDT'),
            ('secretaire general adjoint', 'SGA'),
            ('secretaire generale adjointe', 'SGA'),
            ('secretaire general', 'SG'),
            ('secretaire generale', 'SG'),
            ('tresoriere generale', 'TG'),
            ('tresorier general', 'TG'),
            ('tresoriere adjointe', 'TA'),
            ('tresorier adjoint', 'TA'),
            ('secretaire adjoint', 'SAO'),
            ('secretaire adjointe', 'SAO'),
            ('organisation', 'SO'),
            ('information', 'SIC'),
            ('communication', 'SIC'),
            ('1er commissaire', 'CC1'),
            ('2e commissaire', 'CC2'),
            ('commissaire aux comptes 1', 'CC1'),
            ('commissaire aux comptes 2', 'CC2'),
            ('conseiller juridique', 'CJ'),
            ('directeur technique adjoint', 'DTA'),
            ('directeur technique', 'DT'),
            ('entraineur', 'ENT'),
            ('entraîneur', 'ENT'),
        ]
        
        for kw, sigle in SIGLES:
            if kw in f_lower:
                return sigle
                
        if len(f) <= 5:
            return f.upper()
            
        return f
