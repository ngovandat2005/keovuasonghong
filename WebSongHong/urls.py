from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from main import views
from main.sitemaps import sitemaps


def robots_txt(request):
    lines = [
        'User-agent: *',
        '# Cho phép các trang công khai (kể cả trang con)',
        'Allow: /',
        'Allow: /gioi-thieu/',
        'Allow: /san-pham/',
        'Allow: /tin-tuc/',
        'Allow: /du-an/',
        'Allow: /dai-ly-phan-phoi/',
        'Allow: /dang-ky-dai-ly/',
        'Allow: /e-catalog/',
        'Allow: /cong-cu-tinh/',
        'Allow: /lien-he/',
        'Allow: /chinh-sach-va-dieu-khoan/',
        'Allow: /media/',
        'Allow: /static/',
        '',
        '# Chặn khu vực quản trị, API và các trang xuất dữ liệu',
        'Disallow: /admin/',
        'Disallow: /api/',
        'Disallow: /xuat-excel-tu-van/',
        'Disallow: /xuat-word-tu-van/',
        'Disallow: /dang-ky-tu-van/',
        'Disallow: /404/',
        '',
        'Sitemap: ' + request.build_absolute_uri('/sitemap.xml'),
    ]
    return HttpResponse(chr(10).join(lines), content_type='text/plain')

urlpatterns = [
    path('admin/account/profile/', views.admin_account_profile, name='admin_account_profile'),
    path('admin/notifications/', views.admin_notifications, name='admin_notifications'),
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path('', include('main.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'main.views.custom_404_view'
