from django import template

register = template.Library()


@register.filter
def dict_lookup(dictionnaire, cle):
    """Retourne dictionnaire.get(cle), pour accéder à une valeur par clé dynamique dans un template."""
    if not dictionnaire:
        return None
    return dictionnaire.get(cle)
