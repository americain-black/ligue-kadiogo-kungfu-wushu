from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('practitioners', '0003_grade_ordre_non_unique'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='grade',
            unique_together=set(),
        ),
    ]
