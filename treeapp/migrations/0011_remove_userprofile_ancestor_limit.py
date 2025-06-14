# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('treeapp', '0010_userprofile_ancestor_limit'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='ancestor_limit',
        ),
    ]