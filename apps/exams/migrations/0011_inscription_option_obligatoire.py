from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0010_inscription_motif_exclusion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inscription',
            name='option',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='inscriptions',
                to='exams.optionexamen',
            ),
        ),
    ]
