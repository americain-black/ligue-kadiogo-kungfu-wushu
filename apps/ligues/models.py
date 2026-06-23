
from django.db import models


class Ligue(models.Model):
    nom_ligue            = models.CharField(max_length=200)
    sigle                = models.CharField(max_length=20)
    region               = models.CharField(max_length=100)
    adresse_siege        = models.CharField(max_length=200, blank=True)
    email_contact        = models.EmailField(blank=True)
    telephone            = models.CharField(max_length=20, blank=True)
    nom_directeur_adm    = models.CharField(max_length=100, blank=True)
    nom_directeur_tech   = models.CharField(max_length=100, blank=True)
    nom_secretaire       = models.CharField(max_length=100, blank=True)
    contact_secretaire   = models.CharField(max_length=20,  blank=True)
    logo                 = models.ImageField(upload_to='ligues/', null=True, blank=True)
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