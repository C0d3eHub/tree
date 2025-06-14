# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('treeapp', '0018_merge_20250605_1450'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='email_verification_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]