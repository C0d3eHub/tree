# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('treeapp', '0014_merge_20250604_1645'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='member_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='member_id_for_users', to='treeapp.familymember'),
        ),
    ]