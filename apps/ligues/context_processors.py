from .models import Ligue


def ligue_active(request):
    ligue = Ligue.objects.filter(sigle='LKKFW').first() or Ligue.objects.first()
    return {'ligue_site': ligue}
