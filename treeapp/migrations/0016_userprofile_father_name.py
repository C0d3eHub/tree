# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treeapp', '0015_userprofile_member_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='father_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]