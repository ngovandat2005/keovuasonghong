from django.db import migrations
from django.utils.text import slugify


def backfill(apps, schema_editor):
    Distributor = apps.get_model('main', 'Distributor')
    DistributorDetail = apps.get_model('main', 'DistributorDetail')
    for dist in Distributor.objects.filter(detail__isnull=True):
        base = slugify(dist.name) or 'dai-ly'
        slug, n = base, 1
        while DistributorDetail.objects.filter(slug=slug).exists():
            n += 1
            slug = f'{base}-{n}'
        DistributorDetail.objects.create(distributor=dist, slug=slug)


class Migration(migrations.Migration):
    dependencies = [('main', '0058_productfaq_table')]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
