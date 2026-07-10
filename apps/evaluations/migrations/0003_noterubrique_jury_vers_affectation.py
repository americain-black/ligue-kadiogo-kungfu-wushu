from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('evaluations', '0002_noterubrique_correction_demandee'),
        ('exams', '0010_inscription_motif_exclusion'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='noterubrique',
            name='jury',
        ),
        migrations.AddField(
            model_name='noterubrique',
            name='affectation',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='notes',
                to='exams.affectationjury',
            ),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='noterubrique',
            unique_together={('inscription', 'rubrique_grade')},
        ),
    ]
