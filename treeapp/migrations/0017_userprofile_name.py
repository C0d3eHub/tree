# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treeapp', '0016_userprofile_father_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]