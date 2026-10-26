from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0062_distributordetail_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediaupload',
            name='alt',
            field=models.CharField(blank=True, max_length=300, verbose_name='Alt text (mô tả cho Google)'),
        ),
        migrations.AlterField(
            model_name='mediaupload',
            name='name',
            field=models.CharField(blank=True, max_length=300, verbose_name='Tên ảnh'),
        ),
    ]
