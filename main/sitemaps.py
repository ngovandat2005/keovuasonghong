from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import DistributorDetail, News, Product, Project


class StaticViewSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return ['home', 'about', 'product_list', 'news_list', 'project_list', 'distributors',
                'dealer_register', 'contact', 'catalogue', 'calculator', 'policy']

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True, category__isnull=False).select_related('category')

    def location(self, obj):
        return reverse('product_detail', args=[obj.category.slug, obj.slug])


class NewsSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return News.objects.filter(is_active=True, category__isnull=False).select_related('category')

    def location(self, obj):
        return reverse('news_detail', args=[obj.category.slug, obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class ProjectSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return Project.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('project_detail', args=[obj.category, obj.slug])

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
