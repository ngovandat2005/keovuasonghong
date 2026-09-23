import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebSongHong.settings')
django.setup()
from main.models import News

n = News.objects.filter(slug='vua-kho-tron-san-la-gi').first()
if n:
    n.video_url = None
    n.save(update_fields=['video_url'])
    print('Reset video_url to None successfully for ID:', n.id)

