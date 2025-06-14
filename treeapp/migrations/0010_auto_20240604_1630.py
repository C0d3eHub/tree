# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('treeapp', '0009_userprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='family_root',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='root_for_users', to='treeapp.familymember'),
        ),
    ]