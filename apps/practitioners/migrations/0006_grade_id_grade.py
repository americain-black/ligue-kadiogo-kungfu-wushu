from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('practitioners', '0005_pratiquant_matricule'),
    ]

    operations = [
        migrations.AddField(
            model_name='grade',
            name='id_grade',
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text='Identifiant séquentiel du grade (auto-incrémenté à la création)',
            ),
        ),
    ]
