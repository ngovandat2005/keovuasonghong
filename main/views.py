import json
import re
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .models import Product, ProductCategory, News, NewsCategory, Banner, Distributor, DealerRegistration, ContactMessage, Project, ProjectCategory, ConsultationRequest, Catalogue, ThemeSettings


def home(request):
    banners = Banner.objects.filter(is_active=True)
    featured_products = list(Product.objects.filter(is_featured=True, is_active=True).order_by('order', 'id')[:6])
    if not featured_products:
        featured_products = list(Product.objects.filter(is_active=True).order_by('order', 'id')[:6])
    
    # Lấy danh sách danh mục dự án & toàn bộ dự án thực tế từ DB
    project_categories = list(ProjectCategory.objects.all())
    all_projects = list(Project.objects.filter(is_active=True).order_by('-is_featured', '-published_at', '-id'))

    # Lấy các bài viết phóng sự thực tế từ Tin tức (đồng bộ với danh mục "Phóng sự thực tế" trong Tin tức)
    phong_su_cat = NewsCategory.objects.filter(slug__in=['phong-su', 'phong-su-thuc-te']).first()
    if phong_su_cat:
        phong_su_db = list(News.objects.filter(category=phong_su_cat, is_active=True).order_by('order', 'id'))
    else:
        phong_su_db = []

    all_video_items = []
    for n in phong_su_db:
        vid_id = n.get_video_id() if hasattr(n, 'get_video_id') else None
        if not vid_id:
            continue
        thumb = n.thumbnail_url()
        all_video_items.append({
            'title': n.title,
            'channel': 'Keo Vữa Sông Hồng - SHK Mortar',
            'video_id': vid_id,
            'thumb': thumb,
            'tag': 'SHK',
            'tag_bg': '#FF7E2E',
            'news_slug': n.slug,
            'auto_thumb': n.is_auto_video_thumbnail(),
        })

    # Chia thành các trang 6 video
    phong_su_pages = [all_video_items[i:i + 6] for i in range(0, len(all_video_items), 6)]

    # Lấy toàn bộ dự án thực tế từ DB và chia theo trang (6 dự án / trang)
    all_projects = list(Project.objects.filter(is_active=True).order_by('-is_featured', '-published_at', '-id'))
    project_pages = [all_projects[i:i + 6] for i in range(0, len(all_projects), 6)]
    if not project_pages:
        project_pages = [[]]

    context = {
        'banners': banners,
        'featured_products': featured_products,
        'all_projects': all_projects,
        'project_pages': project_pages,
        'phong_su_pages': phong_su_pages,
    }
    return render(request, 'main/home.html', context)


def about(request):
    theme_obj = ThemeSettings.load()
    gallery_images = list(theme_obj.gallery_images.all())
    total = len(gallery_images)
    # Giữ đúng bố cục masonry gốc (cột 1: 4 ảnh, cột 2: 5 ảnh, cột 3: 5 ảnh) khi số ảnh không đổi
    if total == 14:
        sizes = [4, 5, 5]
    else:
        base, rem = divmod(total, 3)
        sizes = [base + (1 if i < rem else 0) for i in range(3)]
    gallery_columns = []
    start = 0
    for size in sizes:
        gallery_columns.append(gallery_images[start:start + size])
        start += size
    return render(request, 'main/about.html', {'gallery_columns': gallery_columns})


def product_list(request, category=None):
    query_cat = request.GET.get('category')
    if query_cat and not category:
        url = reverse('product_list_category', kwargs={'category': query_cat})
        return redirect(url)

    if category:
        # Nếu category là slug của 1 sản phẩm cũ, redirect sang link chi tiết chuẩn
        cat_obj = ProductCategory.objects.filter(slug=category).first()
        if not cat_obj:
            old_prod = Product.objects.filter(slug=category, is_active=True).first()
            if old_prod:
                c_slug = old_prod.category.slug if old_prod.category else 'san-pham'
                return redirect('product_detail', category=c_slug, slug=old_prod.slug)

    preferred_order = ['vua-kho-tron-san', 'vua-xay-trat-aac', 'keo-dan-gach-da', 'cat-sach-say-kho']
    all_cats = list(ProductCategory.objects.all())
    categories = sorted(all_cats, key=lambda c: preferred_order.index(c.slug) if c.slug in preferred_order else 99)
    
    cat_meta = {
        'vua-kho-tron-san': {'img': 'img/Vua_kho_chon_san.png', 'name': 'Vữa khô trộn sẵn'},
        'vua-xay-trat-aac': {'img': 'img/Vua_kho.png', 'name': 'Vữa xây AAC'},
        'keo-dan-gach-da': {'img': 'img/keo_dan_gach_c1.png', 'name': 'Keo dán gạch'},
        'cat-sach-say-kho': {'img': 'img/Cat_say.png', 'name': 'Cát sấy khô'},
    }
    
    category_list = []
    for cat in categories:
        meta = cat_meta.get(cat.slug, {'img': 'img/Vua_kho_chon_san.png', 'name': cat.name})
        prods = list(Product.objects.filter(category=cat, is_active=True).order_by('order', 'id'))
        category_list.append({
            'slug': cat.slug,
            'name': meta['name'],
            'image': meta['img'],
            'products': prods,
            'count': len(prods),
        })
        
    all_products = list(Product.objects.filter(is_active=True).order_by('order', 'id'))
    cat_slug = category or ''
    
    return render(request, 'main/product_list.html', {
        'category_list': category_list,
        'all_products': all_products,
        'selected_cat_slug': cat_slug,
    })


def product_detail(request, category, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    correct_cat = product.category.slug if product.category else 'san-pham'
    if category != correct_cat:
        return redirect('product_detail', category=correct_cat, slug=product.slug)

    category_products = Product.objects.filter(category=product.category, is_active=True) if product.category else [product]
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:4]
    related_projects = product.project_set.filter(is_active=True)[:3]
    related_catalogues = product.related_catalogues.filter(is_active=True)[:3]

    # Danh sách media chi tiết: gồm ảnh bìa sản phẩm, video chính và các ảnh/video trong thư viện (gallery)
    gallery_items = list(product.gallery_images.all().order_by('order', 'id'))
    media_list = []

    # 1. Ảnh bìa (ảnh đại diện chính) của sản phẩm
    if product.image:
        media_list.append({
            'type': 'image',
            'url': product.image.url,
            'title': product.name
        })

    # 2. Video URL chính (nếu có)
    if product.video_url and product.video_embed_url():
        if not any(m['type'] == 'video' and m.get('embed_url') == product.video_embed_url() for m in media_list):
            media_list.append({
                'type': 'video',
                'embed_url': product.video_embed_url(),
                'title': f'Video giới thiệu {product.name}'
            })

    # 3. Các media được add trong mục "Ảnh & Video chi tiết" (Gallery)
    for g in gallery_items:
        if g.media_type == 'video' and g.video_embed_url():
            if not any(m['type'] == 'video' and m.get('embed_url') == g.video_embed_url() for m in media_list):
                media_list.append({
                    'type': 'video',
                    'embed_url': g.video_embed_url(),
                    'title': f'Video {product.name}'
                })
        elif g.media_type == 'image' and g.display_url():
            if not any(m['type'] == 'image' and m.get('url') == g.display_url() for m in media_list):
                media_list.append({
                    'type': 'image',
                    'url': g.display_url(),
                    'title': f'Ảnh {product.name}'
                })

    # File E-catalog mở trực tiếp trên tab mới
    doc_ecatalog_url = None
    if product.ecatalog_file:
        doc_ecatalog_url = product.ecatalog_file.url
    elif related_catalogues and related_catalogues[0].file:
        doc_ecatalog_url = related_catalogues[0].file.url
    else:
        cat_group_map = {
            'vua-kho-tron-san': 'Tài liệu vữa khô trộn sẵn',
            'vua-xay-trat-aac': 'Tài liệu vữa dành cho gạch AAC',
            'keo-dan-gach-da': 'Tài liệu keo dán gạch',
            'cat-sach-say-kho': 'Tài liệu cát sấy khô',
        }
        group = cat_group_map.get(product.category.slug if product.category else '', '')
        matching_cat = Catalogue.objects.filter(group_name=group, is_active=True).first() if group else None
        if matching_cat and matching_cat.file:
            doc_ecatalog_url = matching_cat.file.url
        else:
            ho_so = Catalogue.objects.filter(slug='ho-so-nang-luc', is_active=True).first()
            if ho_so and ho_so.file:
                doc_ecatalog_url = ho_so.file.url
            else:
                doc_ecatalog_url = reverse('catalogue')

    # File Chứng chỉ chất lượng mở trực tiếp trên tab mới
    doc_certificate_url = None
    if product.certificate_file:
        doc_certificate_url = product.certificate_file.url
    else:
        ho_so = Catalogue.objects.filter(slug='ho-so-nang-luc', is_active=True).first()
        if ho_so and ho_so.file:
            doc_certificate_url = ho_so.file.url
        else:
            doc_certificate_url = reverse('catalogue')

    first_media = media_list[0] if media_list else None

    return render(request, 'main/product_detail.html', {
        'product': product,
        'category_products': category_products,
        'related': related,
        'related_projects': related_projects,
        'related_catalogues': related_catalogues,
        'media_list': media_list,
        'first_media': first_media,
        'doc_ecatalog_url': doc_ecatalog_url,
        'doc_certificate_url': doc_certificate_url,
    })


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def news_list(request, category=None):
    query_cat = request.GET.get('category')
    if query_cat and not category:
        page_param = request.GET.get('page')
        url = reverse('news_list_category', kwargs={'category': query_cat})
        if page_param:
            url += f'?page={page_param}'
        return redirect(url)

    if category:
        # Nếu category là slug của 1 bài viết cũ, redirect sang link chi tiết chuẩn
        cat_obj = NewsCategory.objects.filter(slug=category).first()
        if not cat_obj:
            old_news = News.objects.filter(slug=category, is_active=True).first()
            if old_news:
                c_slug = old_news.category.slug if old_news.category else 'tin-tuc'
                return redirect('news_detail', category=c_slug, slug=old_news.slug)

    preferred_order = ['phong-su-thuc-te', 'kien-thuc-chuyen-mon', 'van-hoa-doanh-nghiep']
    categories = list(NewsCategory.objects.all())
    categories.sort(key=lambda c: preferred_order.index(c.slug) if c.slug in preferred_order else 99)
    
    cat_slug = category or ''
    if cat_slug:
        cat_item = get_object_or_404(NewsCategory, slug=cat_slug)
        news_qs = News.objects.filter(category=cat_item, is_active=True).order_by('-published_at', '-id')
    else:
        cat_item = None
        news_qs = News.objects.filter(is_active=True).order_by('-published_at', '-id')
        
    paginator = Paginator(news_qs, 9)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.get_page(1)
        
    news_items = page_obj

    return render(request, 'main/news_list.html', {
        'news_items': news_items,
        'page_obj': page_obj,
        'categories': categories,
        'current_category': cat_item,
        'selected_cat_slug': cat_slug,
    })


def news_detail(request, category, slug):
    news = get_object_or_404(News, slug=slug, is_active=True)
    correct_cat = news.category.slug if news.category else 'tin-tuc'
    if category != correct_cat:
        return redirect('news_detail', category=correct_cat, slug=news.slug)

    related = news.related_articles.filter(is_active=True)[:4]
    if not related:
        related = News.objects.filter(category=news.category, is_active=True).exclude(pk=news.pk)[:4]
    featured_news = News.objects.filter(is_active=True).exclude(pk=news.pk).order_by('-published_at')[:5]
    categories = NewsCategory.objects.all()
    return render(request, 'main/news_detail.html', {
        'news': news,
        'related': related,
        'featured_news': featured_news,
        'categories': categories,
        'related_products': news.related_products.filter(is_active=True)[:4],
        'related_projects': news.related_projects.filter(is_active=True)[:3],
    })


VIETNAM_PROVINCES = [
    'Hà Nội', 'Vĩnh Phúc', 'Bắc Ninh', 'Hưng Yên', 'Hà Nam', 
    'Hải Dương', 'Hải Phòng', 'Thái Bình', 'Nam Định', 'Ninh Bình', 
    'Phú Thọ', 'Lào Cai', 'Yên Bái',
    'An Giang', 'Bà Rịa - Vũng Tàu', 'Bắc Giang', 'Bắc Kạn', 'Bạc Liêu', 
    'Bến Tre', 'Bình Định', 'Bình Dương', 'Bình Phước', 'Bình Thuận', 
    'Cà Mau', 'Cần Thơ', 'Cao Bằng', 'Đà Nẵng', 'Đắk Lắk', 'Đắk Nông', 
    'Điện Biên', 'Đồng Nai', 'Đồng Tháp', 'Gia Lai', 'Hà Giang', 'Hà Tĩnh', 
    'Hậu Giang', 'Hòa Bình', 'Khánh Hòa', 'Kiên Giang', 'Kon Tum', 
    'Lai Châu', 'Lâm Đồng', 'Lạng Sơn', 'Long An', 'Nghệ An', 'Ninh Thuận', 
    'Phú Yên', 'Quảng Bình', 'Quảng Nam', 'Quảng Ngãi', 'Quảng Ninh', 
    'Quảng Trị', 'Sóc Trăng', 'Sơn La', 'Tây Ninh', 'Thái Nguyên', 
    'Thanh Hóa', 'Thừa Thiên Huế', 'Tiền Giang', 'TP Hồ Chí Minh', 
    'Trà Vinh', 'Tuyên Quang', 'Vĩnh Long'
]

VIETNAM_PROVINCE_COORDS = {
    'Hà Nội': (21.028511, 105.854167),
    'Hải Phòng': (20.844911, 106.688084),
    'Bắc Ninh': (21.186095, 106.076315),
    'Bắc Giang': (21.273078, 106.194600),
    'Quảng Ninh': (21.006450, 107.292510),
    'Phú Thọ': (21.322744, 105.228020),
    'Vĩnh Phúc': (21.308930, 105.604940),
    'Hải Dương': (20.937340, 106.314560),
    'Hưng Yên': (20.646390, 106.051120),
    'Thái Bình': (20.446350, 106.336580),
    'Nam Định': (20.438889, 106.168333),
    'Hà Nam': (20.545360, 105.912640),
    'Ninh Bình': (20.250614, 105.974454),
    'Thanh Hóa': (19.807860, 105.776380),
    'Nghệ An': (18.673750, 105.681280),
    'Hà Tĩnh': (18.342930, 105.905760),
    'Quảng Bình': (17.476050, 106.599720),
    'Quảng Trị': (16.816667, 107.100000),
    'Thừa Thiên Huế': (16.463713, 107.590866),
    'Đà Nẵng': (16.054407, 108.202167),
    'Quảng Nam': (15.565860, 108.473550),
    'Quảng Ngãi': (15.120470, 108.792320),
    'Bình Định': (13.782967, 109.219663),
    'Phú Yên': (13.088190, 109.317440),
    'Khánh Hòa': (12.238791, 109.196749),
    'Ninh Thuận': (11.564770, 108.988220),
    'Bình Thuận': (10.933333, 108.100000),
    'Kon Tum': (14.350000, 108.000000),
    'Gia Lai': (13.983333, 108.000000),
    'Đắk Lắk': (12.666667, 108.050000),
    'Đắk Nông': (12.000000, 107.683333),
    'Lâm Đồng': (11.940420, 108.458310),
    'Bình Phước': (11.750000, 106.900000),
    'Tây Ninh': (11.300000, 106.100000),
    'Bình Dương': (11.166667, 106.666667),
    'Đồng Nai': (10.957388, 106.842713),
    'Bà Rịa - Vũng Tàu': (10.345990, 107.084260),
    'TP Hồ Chí Minh': (10.776889, 106.700806),
    'Long An': (10.533333, 106.400000),
    'Tiền Giang': (10.366667, 106.350000),
    'Bến Tre': (10.233333, 106.383333),
    'Trà Vinh': (9.933333, 106.333333),
    'Vĩnh Long': (10.250000, 105.966667),
    'Đồng Tháp': (10.450000, 105.633333),
    'An Giang': (10.383333, 105.433333),
    'Kiên Giang': (10.016667, 105.083333),
    'Cần Thơ': (10.033333, 105.783333),
    'Hậu Giang': (9.783333, 105.466667),
    'Sóc Trăng': (9.600000, 105.966667),
    'Bạc Liêu': (9.283333, 105.716667),
    'Cà Mau': (9.176820, 105.152420),
    'Lào Cai': (22.485560, 103.970660),
    'Yên Bái': (21.716667, 104.900000),
    'Điện Biên': (21.383333, 103.016667),
    'Hòa Bình': (20.816667, 105.333333),
    'Lai Châu': (22.400000, 103.466667),
    'Sơn La': (21.325600, 103.918800),
    'Hà Giang': (22.823333, 104.983333),
    'Cao Bằng': (22.666667, 106.250000),
    'Bắc Kạn': (22.150000, 105.833333),
    'Lạng Sơn': (21.850000, 106.750000),
    'Tuyên Quang': (21.816667, 105.216667),
    'Thái Nguyên': (21.592780, 105.844170),
}


def extract_distributor_coords(dist):
    link = dist.google_maps_link or ''
    if link:
        # Format !3d(lat)!4d(lng)
        m = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', link)
        if m:
            return float(m.group(1)), float(m.group(2))
        # Format !2d(lng)!3d(lat)
        m = re.search(r'!2d(-?\d+\.\d+)!3d(-?\d+\.\d+)', link)
        if m:
            return float(m.group(2)), float(m.group(1))
        # Format @lat,lng
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', link)
        if m:
            return float(m.group(1)), float(m.group(2))
        # Format q=lat,lng
        m = re.search(r'[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)', link)
        if m:
            return float(m.group(1)), float(m.group(2))
    
    # Fallback to province coordinates
    if dist.province:
        prov_key = dist.province.strip()
        for p, coords in VIETNAM_PROVINCE_COORDS.items():
            if p.lower() in prov_key.lower() or prov_key.lower() in p.lower():
                return coords
    
    return 21.028511, 105.854167


def distributors(request):
    province = request.GET.get('province', '')
    all_distributors = list(Distributor.objects.filter(is_active=True).order_by('province', 'name').prefetch_related('extra_links'))
    dist_map_data = []
    for dist in all_distributors:
        dist.extra_links_json = json.dumps([{'label': l.label, 'url': l.url} for l in dist.extra_links.all()])
        lat, lng = extract_distributor_coords(dist)
        dist.lat = lat
        dist.lng = lng
        dist_map_data.append({
            'id': dist.id,
            'name': dist.name,
            'address': dist.address,
            'province': dist.province,
            'phone': dist.phone,
            'address_type': 'KHU VỰC PHÂN PHỐI' if dist.address_type == 'distribution_area' else 'ĐỊA CHỈ TRỤ SỞ',
            'hotline_label': dist.hotline_label or 'HOTLINE TƯ VẤN & MUA HÀNG',
            'lat': lat,
            'lng': lng,
            'email': dist.email or '',
            'website': dist.website or '',
            'youtube': dist.youtube_url or '',
            'tiktok': dist.tiktok_url or '',
            'extra_links': [{'label': l.label, 'url': l.url} for l in dist.extra_links.all()]
        })
    return render(request, 'main/distributors.html', {
        'distributors': all_distributors,
        'dist_map_data_json': json.dumps(dist_map_data),
        'provinces': VIETNAM_PROVINCES,
        'selected_province': province,
    })


def dealer_register(request):
    if request.method == 'POST':
        company = request.POST.get('company', '').strip()
        tax_id = request.POST.get('tax_id', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        province = request.POST.get('province_name', '').strip() or request.POST.get('province', '').strip()
        district = request.POST.get('district_name', '').strip() or request.POST.get('district', '').strip()
        ward = request.POST.get('ward_name', '').strip() or request.POST.get('ward', '').strip()
        note = request.POST.get('note', '').strip()

        address_parts = [p for p in [ward, district, province] if p]
        address = ", ".join(address_parts) if address_parts else province
        products = request.POST.getlist('products_distributed')
        products_distributed = ", ".join(products)

        if company and phone and province:
            DealerRegistration.objects.create(
                company=company, tax_id=tax_id, full_name=full_name,
                phone=phone, email=email if email else None,
                address=address, province=province,
                products_distributed=products_distributed,
                note=note if note else None
            )
            # Gửi email thông báo về admin
            try:
                admin_link = 'http://192.168.1.103:8000/admin/main/dealerregistration/'
                subject = f'[SHK] Đăng ký đại lý – {company}'
                rows = [
                    ('Doanh nghiệp', company),
                    ('Người đại diện', full_name or '(chưa điền)'),
                    ('Mã số thuế', tax_id or '(chưa điền)'),
                    ('Điện thoại', phone),
                    ('Email', email or '(chưa điền)'),
                    ('Khu vực', address or province),
                    ('Sản phẩm', products_distributed or '(chưa chọn)'),
                    ('Ghi chú', note or '(không có)'),
                ]
                body = (
                    'Có đăng ký đại lý mới từ website SHK Mortar:\n\n'
                    + '\n'.join(f'{label}: {value}' for label, value in rows)
                    + f'\n\nVào admin để xem chi tiết: {admin_link}'
                )
                rows_html = ''.join(
                    f'<tr><td style="padding:6px 16px 6px 0;color:#666;white-space:nowrap;vertical-align:top;">{label}</td>'
                    f'<td style="padding:6px 0;color:#111;font-weight:600;">{value}</td></tr>'
                    for label, value in rows
                )
                html_body = f'''
                <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;">
                    <h2 style="color:#1a2a5e;border-bottom:2px solid #f26522;padding-bottom:10px;">Đăng ký đại lý</h2>
                    <table style="width:100%;border-collapse:collapse;font-size:14px;margin-top:10px;">
                        {rows_html}
                    </table>
                    <p style="margin-top:20px;">
                        <a href="{admin_link}" style="color:#f26522;">Vào admin để xem chi tiết</a>
                    </p>
                    <p style="color:#999;font-size:12px;margin-top:10px;border-top:1px solid #eee;padding-top:10px;">
                        Thời gian đăng ký: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
                    </p>
                </div>
                '''
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.NOTIFY_EMAIL],
                          fail_silently=True, html_message=html_body)
            except Exception:
                pass
            messages.success(request, 'Đăng ký đại lý thành công! Chúng tôi sẽ liên hệ với bạn sớm nhất.')
            return redirect('dealer_register')
        else:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc.')
    all_products = Product.objects.filter(is_active=True).order_by('name')
    return render(request, 'main/dealer_register.html', {'all_products': all_products})


def contact(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        message_text = request.POST.get('message', '').strip()
        if full_name and phone and message_text:
            ContactMessage.objects.create(full_name=full_name, phone=phone, email=email, message=message_text)
            messages.success(request, 'Cảm ơn bạn đã liên hệ! Chúng tôi sẽ phản hồi sớm nhất.')
            return redirect('contact')
        else:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin.')
    return render(request, 'main/contact.html')


def catalogue(request):
    group = request.GET.get('group', '')
    catalogues = Catalogue.objects.filter(is_active=True).order_by('group_name', 'order', 'title')
    if group:
        catalogues = catalogues.filter(group_name=group)
    return render(request, 'main/catalogue.html', {
        'catalogues': catalogues,
        'current_group': group,
    })


from django.core.paginator import Paginator

VALID_PROJECT_CATEGORIES = ['dan-dung', 'cong-nghiep']


def project_list(request, category=None):
    # Nếu người dùng vào bằng query ?category=... cũ thì redirect sang URL sạch /du-an/<category>/
    query_cat = request.GET.get('category')
    if query_cat and not category:
        page_param = request.GET.get('page')
        url = reverse('project_list_category', kwargs={'category': query_cat})
        if page_param:
            url += f'?page={page_param}'
        return redirect(url)

    if category:
        # Nếu category không nằm trong danh mục, kiểm tra xem có phải link cũ trỏ thẳng vào slug của 1 dự án không
        if category not in VALID_PROJECT_CATEGORIES:
            old_project = Project.objects.filter(slug=category, is_active=True).first()
            if old_project:
                return redirect('project_detail', category=old_project.category, slug=old_project.slug)

    cat = category or ''
    projects = Project.objects.filter(is_active=True).order_by('-published_at')
    
    if cat:
        projects = projects.filter(category=cat)
        
    paginator = Paginator(projects, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'main/project_list.html', {
        'projects': page_obj.object_list,
        'page_obj': page_obj,
        'current_category': cat,
    })


def project_category_redirect(request, category):
    page_param = request.GET.get('page')
    url = reverse('project_list_category', kwargs={'category': category})
    if page_param:
        url += f'?page={page_param}'
    return redirect(url)


def project_detail(request, category, slug):
    project = get_object_or_404(Project, slug=slug, is_active=True)
    if project.category and project.category != category:
        return redirect('project_detail', category=project.category, slug=project.slug)
    related_catalogues = project.related_catalogues.filter(is_active=True)[:3]
    return render(request, 'main/project_detail.html', {
        'project': project,
        'related_catalogues': related_catalogues,
    })


def consultation(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        province = request.POST.get('province', '').strip() or request.POST.get('area', '').strip()
        district = request.POST.get('district', '').strip()
        address_detail = request.POST.get('address_detail', '').strip()
        company = request.POST.get('company', '').strip()
        interest = request.POST.get('interest', '').strip()
        message_text = request.POST.get('message', '').strip()

        referer = request.META.get('HTTP_REFERER') or 'home'

        # Check required fields
        if not full_name or not phone or not province or not (interest or message_text):
            messages.error(request, 'Vui lòng điền đầy đủ các thông tin bắt buộc (*).')
            return redirect(referer)

        # Validate phone format (10 digits Vietnam phone number)
        phone_cleaned = re.sub(r'[\s.-]', '', phone)
        if not re.match(r'^(0[235789])[0-9]{8}$', phone_cleaned):
            messages.error(request, 'Số điện thoại không hợp lệ. Vui lòng nhập số điện thoại gồm 10 chữ số (VD: 0912345678).')
            return redirect(referer)

        # Validate email strictly if provided
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]+([.-][a-zA-Z0-9]+)*\.[a-zA-Z]{2,}$', email):
            messages.error(request, 'Địa chỉ email không đúng định dạng. Vui lòng kiểm tra lại tên miền (VD: example@gmail.com).')
            return redirect(referer)

        # Check duplicate submission within 1 hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_duplicate = ConsultationRequest.objects.filter(
            phone=phone_cleaned,
            created_at__gte=one_hour_ago
        ).exists()

        if recent_duplicate:
            messages.warning(request, 'Thông tin đăng ký của số điện thoại này đã được tiếp nhận gần đây. Đội ngũ chuyên viên của SHK Mortar sẽ liên hệ sớm nhất!')
            return redirect(referer)

        # Build full address string
        area_parts = [p for p in [province, district, address_detail] if p]
        area_full = ", ".join(area_parts)

        full_message_parts = []
        if area_full:
            full_message_parts.append(f"Khu vực: {area_full}")
        if interest or message_text:
            full_message_parts.append(f"Nhu cầu: {interest or message_text}")
        full_message = "\n".join(full_message_parts)

        consultation_obj = ConsultationRequest.objects.create(
            full_name=full_name, phone=phone_cleaned, email=email,
            company=company, interest=interest or province or "Tư vấn sản phẩm", message=full_message
        )

        # Gửi email thông báo về admin
        try:
            subject = f'[SHK] Đăng ký tư vấn mới – {full_name} ({phone_cleaned})'
            body = (
                f'Có đăng ký tư vấn mới từ website SHK Mortar:\n\n'
                f'Họ tên      : {full_name}\n'
                f'Điện thoại  : {phone_cleaned}\n'
                f'Email       : {email or "(chưa điền)"}\n'
                f'Công ty     : {company or "(chưa điền)"}\n'
                f'Khu vực     : {area_full or "(chưa điền)"}\n'
                f'Quan tâm    : {interest or "(chưa điền)"}\n'
                f'Nội dung    : {message_text or "(không có)"}\n\n'
                f'Vào admin để xem chi tiết: http://192.168.1.103:8000/admin/main/consultationrequest/'
            )
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.NOTIFY_EMAIL], fail_silently=True)
        except Exception:
            pass

        # Tự động xuất và cập nhật ra file Excel và Word
        try:
            from .export_utils import auto_save_consultation_to_files
            auto_save_consultation_to_files(consultation_obj)
        except Exception:
            pass

        messages.success(request, 'Đăng ký tư vấn thành công! Chuyên viên của SHK Mortar sẽ liên hệ với bạn trong thời gian sớm nhất.')
        return redirect(referer)

    products = Product.objects.filter(is_active=True).values('name')
    return render(request, 'main/consultation.html', {'products': products})


def download_consultations_excel(request):
    """Tải file Excel danh sách khách hàng đăng ký tư vấn"""
    from .export_utils import export_consultations_to_excel
    queryset = ConsultationRequest.objects.all().order_by('-created_at')
    wb = export_consultations_to_excel(queryset)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="Danh_Sach_Dang_Ky_Tu_Van_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
    wb.save(response)
    return response


def download_consultation_word(request, pk):
    """Tải file Word phiếu yêu cầu tư vấn cho 1 khách hàng cụ thể"""
    from io import BytesIO
    from .export_utils import export_consultation_to_docx
    consultation_obj = get_object_or_404(ConsultationRequest, pk=pk)
    doc = export_consultation_to_docx(consultation_obj)
    
    doc_io = BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    
    response = HttpResponse(
        doc_io.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    safe_phone = str(consultation_obj.phone).replace(' ', '')
    response['Content-Disposition'] = f'attachment; filename="Phieu_Tu_Van_SHK_{consultation_obj.pk}_{safe_phone}.docx"'
    return response



CALCULATOR_PRODUCT_MAP = {
    'mortar': ['vua-kho-tron-san', 'vua-tieu-chuan', 'vua-cao-cap'],
    'tile_adhesive': ['keo-dan-gach', 'keo-noi-that', 'keo-ngoai-troi'],
    'sand': ['cat-say', 'cat-0-06mm', 'cat-0-2mm'],
}

def calculator(request):
    result = None
    recommended_products = []
    if request.method == 'POST':
        tool = request.POST.get('tool')
        try:
            if tool == 'mortar':
                area = float(request.POST.get('area', 0))
                thickness = float(request.POST.get('thickness', 10))
                result = {'label': 'Lượng vữa cần dùng', 'value': f'{area * thickness * 1.85:.1f} kg', 'tool': tool, 'tool_name': 'Vữa khô trộn sẵn'}
            elif tool == 'tile_adhesive':
                area = float(request.POST.get('area', 0))
                tile_size = request.POST.get('tile_size', 'small')
                rate = {'small': 4.5, 'medium': 5.5, 'large': 7.0}.get(tile_size, 5.0)
                result = {'label': 'Lượng keo dán gạch cần dùng', 'value': f'{area * rate:.1f} kg', 'tool': tool, 'tool_name': 'Keo dán gạch'}
            elif tool == 'sand':
                area = float(request.POST.get('area', 0))
                thickness = float(request.POST.get('thickness', 10))
                result = {'label': 'Lượng cát cần dùng', 'value': f'{area * (thickness / 1000) * 1600:.1f} kg', 'tool': tool, 'tool_name': 'Cát sấy khô'}
            if result and tool:
                category_slugs = CALCULATOR_PRODUCT_MAP.get(tool, [])
                recommended_products = Product.objects.filter(
                    is_active=True, category__slug__in=category_slugs
                )[:3]
                if not recommended_products:
                    cat_map = {'mortar': 'vua-kho-tron-san', 'tile_adhesive': 'keo-dan-gach', 'sand': 'cat-say'}
                    recommended_products = Product.objects.filter(
                        is_active=True, category__slug=cat_map.get(tool, '')
                    )[:3]
                    if not recommended_products:
                        recommended_products = Product.objects.filter(is_active=True)[:3]
        except (ValueError, ZeroDivisionError):
            messages.error(request, 'Vui lòng nhập số liệu hợp lệ.')
    return render(request, 'main/calculator.html', {'result': result, 'recommended_products': recommended_products})


@login_required(login_url='/admin/login/')
def admin_account_profile(request):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")

    from .models import UserProfile
    profile = UserProfile.get_for_user(request.user)

    if request.method == 'POST':
        action = request.POST.get('action', 'save_profile')
        if action == 'change_password':
            from django.contrib.auth import update_session_auth_hash
            from django.contrib.auth.forms import PasswordChangeForm
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Đổi mật khẩu thành công!')
                return redirect('/admin/account/profile/')
            else:
                for error_list in form.errors.values():
                    for err in error_list:
                        messages.error(request, err)
        else:
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            birthday = request.POST.get('birthday', '').strip() or None
            gender = request.POST.get('gender', 'Nam').strip()
            region = request.POST.get('region', '').strip()
            ward = request.POST.get('ward', '').strip()
            address = request.POST.get('address', '').strip()

            profile.full_name = full_name
            profile.phone = phone
            profile.email = email
            profile.birthday = birthday
            profile.gender = gender
            profile.region = region
            profile.ward = ward
            profile.address = address
            profile.save()

            if full_name:
                parts = full_name.split(' ', 1)
                request.user.first_name = parts[0]
                request.user.last_name = parts[1] if len(parts) > 1 else ''
            if email:
                request.user.email = email
            request.user.save()

            messages.success(request, 'Cập nhật thông tin tài khoản thành công!')
            return redirect('/admin/account/profile/')

    context = {
        'profile': profile,
        'title': 'Thông tin tài khoản',
        'has_permission': True,
        'is_nav_sidebar_enabled': True,
    }
    return render(request, 'admin/account/profile.html', context)


def policy(request):
    return render(request, 'main/policy.html')

