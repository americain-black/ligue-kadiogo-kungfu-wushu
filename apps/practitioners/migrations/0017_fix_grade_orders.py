from django.db import migrations

def fix_grade_orders(apps, schema_editor):
    Grade = apps.get_model('practitioners', 'Grade')
    # Regrouper par ligue et renuméroter les ordres pour éviter les doublons
    for grade in Grade.objects.all():
        if grade.ordre == 0 or grade.ordre is None:
            grade.ordre = grade.id_grade or 1
            grade.save()

    # S'assurer que chaque grade dans une ligue a un ordre unique séquentiel
    from django.db.models import Count
    ligue_ids = Grade.objects.values_list('ligue_id', flat=True).distinct()
    for ligue_id in ligue_ids:
        grades = Grade.objects.filter(ligue_id=ligue_id).order_by('id_grade', 'id')
        seen_ordres = set()
        for idx, g in enumerate(grades, start=1):
            if g.ordre in seen_ordres or g.ordre == 0:
                g.ordre = idx
                g.save()
            else:
                seen_ordres.add(g.ordre)

def reverse_fix(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('practitioners', '0016_alter_grade_options_grade_ordre'),
    ]

    operations = [
        migrations.RunPython(fix_grade_orders, reverse_code=reverse_fix),
    ]
