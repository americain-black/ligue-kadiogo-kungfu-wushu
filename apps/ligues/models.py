
from django.db import models


class Ligue(models.Model):
    nom_ligue            = models.CharField(max_length=200, unique=True)
    sigle                = models.CharField(max_length=20,unique=True)
    region               = models.CharField(max_length=100)
    adresse_siege = models.CharField(max_length=200, blank=True)
    email_contact = models.EmailField(blank=True)
    telephone     = models.CharField(max_length=20, blank=True)
    logo          = models.ImageField(upload_to='ligues/', null=True, blank=True)
    statut               = models.CharField(
        max_length=20,
        choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')],
        default='ACTIVE'
    )
    date_creation        = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Ligue'
        verbose_name_plural = 'Ligues'

    def __str__(self):
        return f"{self.sigle} — {self.nom_ligue}"

    def est_active(self):
        return self.statut == 'ACTIVE'


class VoletOrganigramme(models.Model):
    ligue       = models.ForeignKey(Ligue, on_delete=models.CASCADE, related_name='volets')
    nom_volet   = models.CharField(max_length=200)
    ordre       = models.PositiveIntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Volet organigramme'
        verbose_name_plural = 'Volets organigramme'
        ordering            = ['ordre', 'date_creation']

    def __str__(self):
        return f"{self.ligue.sigle} — {self.nom_volet}"


class MembreOrganigramme(models.Model):
    volet      = models.ForeignKey(VoletOrganigramme, on_delete=models.CASCADE, related_name='membres')
    nom                = models.CharField(max_length=100)
    prenom             = models.CharField(max_length=100)
    contact            = models.CharField(max_length=50, blank=True)
    fonction           = models.CharField(max_length=200)
    date_debut_fonction = models.DateField(null=True, blank=True)
    actif              = models.BooleanField(default=True)
    date_ajout         = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Membre organigramme'
        verbose_name_plural = 'Membres organigramme'
        ordering            = ['-actif', 'nom', 'prenom']

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.fonction}"