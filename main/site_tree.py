"""Quét toàn bộ danh mục / trang con hiện có và dựng thành cây phân cấp để hiển thị sơ đồ trang (HTML sitemap).

Mỗi nút là dict: {'title': str, 'url': str | None, 'children': [nút, ...]}.
Nội dung lấy trực tiếp từ database nên thêm/xóa sản phẩm, dự án, tin tức, đại lý... sẽ tự cập nhật.
"""
from django.urls import reverse

from .models import (
    DistributorDetail, News, NewsCategory, Product, ProductCategory,
    Project, PROJECT_CATEGORY_CHOICES,
)


def _node(title, url=None, children=None):
    return {'title': title, 'url': url, 'children': children or []}


def _products_branch():
    categories = ProductCategory.objects.all().order_by('id')
    products = list(Product.objects.filter(is_active=True).only('name', 'slug', 'category_id').order_by('order', 'id'))

    children = []
    for cat in categories:
        items = [_node(p.name, reverse('product_detail', args=[p.slug])) for p in products if p.category_id == cat.id]
        children.append(_node(cat.name, reverse('product_list_category', args=[cat.slug]), items))

    # Sản phẩm chưa gán danh mục: đặt ngay dưới "Sản phẩm"
    known_ids = {c.id for c in categories}
    children += [_node(p.name, reverse('product_detail', args=[p.slug])) for p in products if p.category_id not in known_ids]
    return _node('Sản phẩm', reverse('product_list'), children)


def _projects_branch():
    projects = list(Project.objects.filter(is_active=True).only('title', 'slug', 'category').order_by('-published_at'))
    children = []
    for slug, label in PROJECT_CATEGORY_CHOICES:
        items = [_node(p.title, reverse('project_detail', args=[p.slug])) for p in projects if p.category == slug]
        children.append(_node(label, reverse('project_list_category', args=[slug]), items))
    return _node('Dự án', reverse('project_list'), children)


def _distributors_branch():
    details = (DistributorDetail.objects.filter(is_active=True, distributor__is_active=True)
               .select_related('distributor').order_by('distributor__province', 'distributor__name'))
    by_province = {}
    for d in details:
        by_province.setdefault(d.distributor.province or 'Khác', []).append(
            _node(d.title or d.distributor.name, d.get_absolute_url()))
    children = [_node(province, None, items) for province, items in by_province.items()]
    return _node('Đại lý phân phối', reverse('distributors'), children)


def _news_branch():
    categories = list(NewsCategory.objects.all().order_by('id'))
    news = list(News.objects.filter(is_active=True).only('title', 'slug', 'category_id').order_by('-published_at', '-id'))
    children = []
    for cat in categories:
        items = [_node(n.title, reverse('news_detail', args=[n.slug])) for n in news if n.category_id == cat.id]
        children.append(_node(cat.name, reverse('news_list_category', args=[cat.slug]), items))
    known_ids = {c.id for c in categories}
    children += [_node(n.title, reverse('news_detail', args=[n.slug])) for n in news if n.category_id not in known_ids]
    return _node('Tin tức', reverse('news_list'), children)


def build_site_tree():
    return [
        _node('Trang chủ', reverse('home')),
        _node('Giới thiệu', reverse('about')),
        _products_branch(),
        _projects_branch(),
        _distributors_branch(),
        _node('E-Catalog', reverse('catalogue')),
        _node('Công cụ tính', reverse('calculator')),
        _news_branch(),
        _node('Đăng ký đại lý', reverse('dealer_register')),
        _node('Liên hệ', reverse('contact')),
        _node('Chính sách và điều khoản', reverse('policy')),
    ]


def count_pages(nodes):
    return sum(1 + count_pages(n['children']) for n in nodes)
