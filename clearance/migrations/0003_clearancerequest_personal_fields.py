from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('clearance', '0002_authtoken'),
    ]
    operations = [
        migrations.AddField(
            model_name='clearancerequest',
            name='personal_email',
            field=models.EmailField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='clearancerequest',
            name='personal_phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='clearancerequest',
            name='campus',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
