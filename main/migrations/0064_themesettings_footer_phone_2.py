from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0063_mediaupload_alt'),
    ]

    operations = [
        migrations.AddField(
            model_name='themesettings',
            name='footer_phone_2',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='SĐT footer 2'),
        ),
    ]
