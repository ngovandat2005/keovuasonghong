from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import DistributorDetail, News, Product, Project


class ImageSitemapMixin:
    """Thêm <image:image> vào từng URL để Google lập chỉ mục ảnh cùng trang (dùng template sitemap_images.xml)."""

    def get_images(self, obj):
        return []

    def _urls(self, page, protocol, domain):
        urls = super()._urls(page, protocol, domain)
        for info in urls:
            images = []
            for url, title in self.get_images(info['item']):
                if url:
                    images.append({'loc': url if url.startswith('http') else f"{protocol}://{domain}{url}", 'title': title})
            info['images'] = images
        return urls


def _safe_url(field):
    try:
        return field.url if field else ''
    except Exception:
        return ''


class StaticViewSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return ['home', 'about', 'product_list', 'news_list', 'project_list', 'distributors',
                'dealer_register', 'catalogue', 'calculator', 'policy', 'site_map']

    def location(self, item):
        return reverse(item)


class ProductSitemap(ImageSitemapMixin, Sitemap):
    protocol = 'https'
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return (Product.objects.filter(is_active=True, category__isnull=False)
                .select_related('category').prefetch_related('gallery_images'))

    def get_images(self, obj):
        images = [(_safe_url(obj.image), obj.name)]
        for gi in obj.gallery_images.all():
            if gi.media_type == 'image':
                images.append((gi.display_url(), obj.name))
        return images

    def location(self, obj):
        return reverse('product_detail', args=[obj.slug])


class NewsSitemap(ImageSitemapMixin, Sitemap):
    protocol = 'https'
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return News.objects.filter(is_active=True, category__isnull=False).select_related('category')

    def get_images(self, obj):
        return [(_safe_url(obj.image), obj.title)]

    def location(self, obj):
        return reverse('news_detail', args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class ProjectSitemap(ImageSitemapMixin, Sitemap):
    protocol = 'https'
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return Project.objects.filter(is_active=True)

    def get_images(self, obj):
        return [(_safe_url(obj.image), obj.title)]

    def location(self, obj):
        return reverse('project_detail', args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class DistributorSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return DistributorDetail.objects.filter(is_active=True, distributor__is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    'static': StaticViewSitemap,
    'san-pham': ProductSitemap,
    'tin-tuc': NewsSitemap,
    'du-an': ProjectSitemap,
    'dai-ly': DistributorSitemap,
}
