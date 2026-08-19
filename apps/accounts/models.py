









from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Permission(models.Model):
    """Action précise possible dans le système"""

    code = models.SlugField(max_length=100, unique=True)
    nom_permission = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        ordering = ['module', 'code']

    def __str__(self):
        return f"{self.code} ({self.module})"


class Role(models.Model):
    """Rôle attribuable à un utilisateur"""

    SUPER_ADMIN    = 'SUPER_ADMIN'
    GEST_LIGUE     = 'GEST_LIGUE'
    GEST_TECHNIQUE = 'GEST_TECHNIQUE'
    GEST_FINANCIER = 'GEST_FINANCIER'
    GEST_COM       = 'GEST_COM'
    GEST_CLUB      = 'GEST_CLUB'
    JURY           = 'JURY'

    ROLE_CHOICES = [
        (SUPER_ADMIN,    'Super Administrateur'),
        (GEST_LIGUE,     'Gestionnaire Ligue (Administrateur Principal / SG)'),
        (GEST_TECHNIQUE, 'Responsable Technique Ligue (Examens, Grades)'),
        (GEST_FINANCIER, 'Gestionnaire Financier Ligue'),
        (GEST_COM,       'Chargé de Communication Ligue'),
        (GEST_CLUB,      'Gestionnaire Club'),
        (JURY,           'Membre du Jury / Évaluateur'),
    ]

    nom_role    = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles',
        blank=True
    )

    class Meta:
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"

    def __str__(self):
        return self.get_nom_role_display()

    def a_la_permission(self, code_permission):
        return self.permissions.filter(code=code_permission).exists()


class RolePermission(models.Model):
    """Table de jonction Role <-> Permission"""

    role       = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')
        verbose_name = "Permission du rôle"

    def __str__(self):
        return f"{self.role} → {self.permission}"


class Utilisateur(AbstractUser):
    """
    Modèle utilisateur personnalisé.
    Un utilisateur peut avoir PLUSIEURS rôles (many-to-many via UtilisateurRole).
    """

    # Champs supplémentaires
    SEXE_CHOICES = [
        ('M', 'Masculin / Monsieur'),
        ('F', 'Féminin / Madame'),
    ]
    sexe         = models.CharField(max_length=1, choices=SEXE_CHOICES, default='M', blank=True)
    telephone    = models.CharField(max_length=20, blank=True)
    photo        = models.ImageField(upload_to='profils/', null=True, blank=True)
    statut_compte = models.BooleanField(default=True)

    @property
    def civilite(self):
        return "Madame" if self.sexe == 'F' else "Monsieur"

    # Sécurité
    tentatives_connexion     = models.PositiveSmallIntegerField(default=0)
    token_reinitialisation   = models.UUIDField(default=uuid.uuid4, null=True, blank=True)
    token_expiration         = models.DateTimeField(null=True, blank=True)

    # On utilise 'ligues.Ligue' en string pour éviter l'import circulaire entre apps.
    ligue = models.ForeignKey(
        'ligues.Ligue',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='utilisateurs'
    )

    # Rôles many-to-many via UtilisateurRole
    roles = models.ManyToManyField(
        Role,
        through='UtilisateurRole',
        related_name='utilisateurs',
        blank=True
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.get_full_name() or self.username}"

    # ── Méthodes utilitaires ─────────────────────────────────────────

    def a_le_role(self, nom_role):
        """Vérifie si l'utilisateur possède un rôle donné."""
        return self.roles.filter(nom_role=nom_role).exists()

    def a_la_permission(self, code_permission):
        """
        Vérifie si l'utilisateur possède une permission donnée,
        via l'un quelconque de ses rôles.
        """
        return Permission.objects.filter(
            code=code_permission,
            roles__utilisateurs=self
        ).exists()

    def est_super_admin(self):
        return self.a_le_role(Role.SUPER_ADMIN) or self.is_superuser

    def est_gest_ligue(self):
        return self.is_superuser or self.a_le_role(Role.GEST_LIGUE) or self.a_le_role(Role.GEST_TECHNIQUE) or self.a_le_role(Role.GEST_FINANCIER) or self.a_le_role(Role.GEST_COM)

    def est_gest_ligue_principal(self):
        return self.is_superuser or self.a_le_role(Role.GEST_LIGUE)

    def est_gest_technique(self):
        return self.est_gest_ligue_principal() or self.a_le_role(Role.GEST_TECHNIQUE)

    def est_gest_com(self):
        return self.est_gest_ligue_principal() or self.a_le_role(Role.GEST_COM)

    def est_gest_club(self):
        return self.a_le_role(Role.GEST_CLUB)

    def est_gest_financier(self):
        return self.est_gest_ligue_principal() or self.a_le_role(Role.GEST_FINANCIER)

    def est_jury(self):
        return self.a_le_role(Role.JURY)







    @property
    def libelle_espace_role(self):
        """Retourne la phrase d'espace dédiée selon le rôle de l'utilisateur."""
        if self.is_superuser or self.a_le_role(Role.SUPER_ADMIN):
            return "Espace réservé au Super Administrateur"
        elif self.a_le_role(Role.GEST_LIGUE):
            return "Espace dédié au Gestionnaire de la Ligue"
        elif self.a_le_role(Role.GEST_TECHNIQUE):
            return "Espace dédié à la Direction Technique"
        elif self.a_le_role(Role.GEST_FINANCIER):
            return "Espace dédié au Gestionnaire Financier"
        elif self.a_le_role(Role.GEST_COM):
            return "Espace dédié au Chargé de Communication"
        elif self.a_le_role(Role.GEST_CLUB):
            return "Espace dédié au Gestionnaire de Club"
        elif self.a_le_role(Role.JURY):
            return "Espace dédié au Membre du Jury"
        elif self.est_gest_ligue():
            return "Espace dédié au Gestionnaire de la Ligue"
        return "Espace dédié au Pratiquant / Licencié"

    def get_roles_display(self):
        """Retourne la liste lisible des rôles de l'utilisateur."""
        return [r.get_nom_role_display() for r in self.roles.all()]

    def token_est_valide(self):
        """Vérifie si le token de réinitialisation n'est pas expiré."""
        if not self.token_expiration:
            return False
        return timezone.now() < self.token_expiration



class UtilisateurRole(models.Model):
    """Table de jonction Utilisateur <-> Role"""

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    role        = models.ForeignKey(Role, on_delete=models.CASCADE)
    date_attribution = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('utilisateur', 'role')
        verbose_name = "Rôle utilisateur"
        verbose_name_plural = "Rôles utilisateurs"

    def __str__(self):
        return f"{self.utilisateur} — {self.role}"