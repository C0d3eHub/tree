# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('treeapp', '0012_merge_20250604_1639'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='last_child',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='last_child_for_users', to='treeapp.familymember'),
        ),
    ]