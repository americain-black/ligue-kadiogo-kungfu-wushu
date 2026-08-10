from django.test import TestCase, SimpleTestCase
from django.conf import settings
from apps.ligues.models import Ligue, VoletOrganigramme, MembreOrganigramme
from apps.clubs.models import Club


class OrganigrammeIsolationTest(TestCase):
    def setUp(self):
        self.ligue = Ligue.objects.first()
        if not self.ligue:
            return
        self.club = Club.objects.filter(ligue=self.ligue).first()
        if not self.club:
            self.club = Club.objects.create(
                ligue=self.ligue,
                nom_club="Dragon Club Test",
                sigle_club="DCTest"
            )
        self.volet = VoletOrganigramme.objects.create(
            ligue=self.ligue,
            nom_volet="Bureau Test Isolation"
        )
        self.membre_ligue = MembreOrganigramme.objects.create(
            volet=self.volet,
            nom="Ouedraogo",
            prenom="Jean",
            fonction="PDT",
            club=None
        )
        self.membre_club = MembreOrganigramme.objects.create(
            volet=self.volet,
            nom="Sawadogo",
            prenom="Paul",
            fonction="ENT",
            club=self.club
        )

    def test_ligue_organigram_shows_only_ligue_members(self):
        if not self.ligue:
            return
        ligue_membres = self.volet.membres.filter(club__isnull=True)
        self.assertIn(self.membre_ligue, ligue_membres)
        self.assertNotIn(self.membre_club, ligue_membres)

    def test_club_organigram_shows_only_club_members(self):
        if not self.ligue:
            return
        club_membres = self.volet.membres.filter(club=self.club)
        self.assertIn(self.membre_club, club_membres)
        self.assertNotIn(self.membre_ligue, club_membres)


class ProxySSLSettingsTest(SimpleTestCase):
    def test_secure_proxy_ssl_header_configured(self):
        self.assertEqual(getattr(settings, 'SECURE_PROXY_SSL_HEADER', None), ('HTTP_X_FORWARDED_PROTO', 'https'))
        self.assertTrue(getattr(settings, 'USE_X_FORWARDED_HOST', False))


