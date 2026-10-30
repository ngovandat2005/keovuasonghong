from django.db import migrations, models


def gop_sdt(apps, schema_editor):
    """Gộp "SĐT footer 2" vào ô "SĐT footer" (cách nhau bằng dấu -) trước khi bỏ cột — không mất số đang dùng."""
    ThemeSettings = apps.get_model('main', 'ThemeSettings')
    for t in ThemeSettings.objects.all():
        so = []
        for v in ((t.footer_phone or ''), (t.footer_phone_2 or '')):
            v = v.strip()
            if v and v not in so:
                so.append(v)
        gop = ' - '.join(so)
        if gop != (t.footer_phone or ''):
            t.footer_phone = gop
            t.save(update_fields=['footer_phone'])


def khong_lam_gi(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0064_themesettings_footer_phone_2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='themesettings',
            name='footer_phone',
            field=models.CharField(blank=True, default='0938016788', help_text='Nhập nhiều số thì cách nhau bằng dấu -, ví dụ: 0938016788 - 0386360797. Mỗi số hiện thành một link gọi riêng ở footer.', max_length=100, null=True, verbose_name='SĐT footer'),
        ),
        migrations.RunPython(gop_sdt, khong_lam_gi),
        migrations.RemoveField(
            model_name='themesettings',
            name='footer_phone_2',
        ),
    ]
