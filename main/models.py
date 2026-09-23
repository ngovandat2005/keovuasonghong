import html
import re
import unicodedata
from django.db import models
from django.utils.text import slugify


def vietnamese_slugify(text):
    if not text:
        return ""
    text = str(text).lower().strip()
    text = text.replace('đ', 'd').replace('Đ', 'd')
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')


def clean_html_excerpt(text, max_words=None):
    if not text:
        return ""
    s = str(text)
    # Double unescape to handle doubly-encoded entities like &amp;ocirc;
    s = html.unescape(s)
    s = html.unescape(s)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = s.replace('\xa0', ' ').replace('&nbsp;', ' ')
    s = ' '.join(s.split())
    if max_words:
        words = s.split()
        if len(words) > max_words:
            return ' '.join(words[:max_words]) + '...'
    return s


def clean_video_url(url):
    if not url:
        return ''
    u = str(url).strip()
    if '<iframe' in u and 'src=' in u:
        m = re.search(r'src=["\']([^"\']+)["\']', u)
        if m:
            u = m.group(1)
    if u and not u.startswith(('http://', 'https://')) and ('youtube.com' in u or 'youtu.be' in u):
        u = 'https://' + u
    return u


def youtube_embed_url(url):
    if not url:
        return None
    url = url.strip()
    if '<iframe' in url and 'src=' in url:
        import re
        m = re.search(r'src=["\']([^"\']+)["\']', url)
        if m:
            url = m.group(1)
    if not url.startswith(('http://', 'https://')) and ('youtube.com' in url or 'youtu.be' in url):
        url = 'https://' + url
    if 'youtu.be/' in url:
        vid = url.split('youtu.be/')[-1].split('?')[0].split('&')[0]
    elif 'youtube.com/watch' in url:
        import urllib.parse
        qs = urllib.parse.urlparse(url).query
        vid = urllib.parse.parse_qs(qs).get('v', [None])[0]
    elif 'youtube.com/shorts/' in url:
        vid = url.split('youtube.com/shorts/')[-1].split('?')[0].split('&')[0]
    elif 'youtube.com/embed/' in url:
        vid = url.split('youtube.com/embed/')[-1].split('?')[0].split('&')[0]
    elif 'youtube-nocookie.com/embed/' in url:
        vid = url.split('youtube-nocookie.com/embed/')[-1].split('?')[0].split('&')[0]
    elif len(url) == 11 and ' ' not in url and '/' not in url:
        vid = url
    else:
        return None
    return f'https://www.youtube.com/embed/{vid}?rel=0' if vid else None



class ProductCategory(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Danh mục sản phẩm"
        verbose_name_plural = "Danh mục sản phẩm"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=300, verbose_name="Tên sản phẩm")
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Mã SKU")
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Danh mục")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Hình ảnh")
    video_url = models.URLField(blank=True, null=True, verbose_name="Link video YouTube")
    ecatalog_file = models.FileField(upload_to='products/ecatalog/', blank=True, null=True, verbose_name="File E-catalog (PDF)")
    certificate_file = models.FileField(upload_to='products/certificates/', blank=True, null=True, verbose_name="Chứng chỉ chất lượng (PDF)")
    short_description = models.TextField(blank=True, verbose_name="Đoạn giới thiệu tổng quan")
    description = models.TextField(blank=True, verbose_name="Hướng dẫn thi công")
    usage_norms = models.TextField(blank=True, verbose_name="Định mức sử dụng")
    specifications = models.TextField(blank=True, verbose_name="Thông tin sản phẩm")
    order = models.IntegerField(default=0, verbose_name="Thứ tự")
    is_featured = models.BooleanField(default=False, verbose_name="Sản phẩm nổi bật")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"
        ordering = ['order', 'id']

    def clean(self):
        super().clean()
        if not self.sku or not str(self.sku).strip():
            self.sku = None
        if self.video_url:
            self.video_url = clean_video_url(self.video_url)

    def save(self, *args, **kwargs):
        if not self.sku or not str(self.sku).strip():
            self.sku = None
        if self.video_url:
            self.video_url = clean_video_url(self.video_url)
        if not self.slug:
            base_slug = slugify(self.name) or "san-pham"
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def video_embed_url(self):
        return youtube_embed_url(self.video_url)

    @property
    def display_short_description(self):
        return clean_html_excerpt(self.short_description, 20)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    MEDIA_TYPE_CHOICES = [('image', 'Ảnh'), ('video', 'Video')]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='image', verbose_name="Loại")
    image = models.ImageField(upload_to='products/gallery/', blank=True, null=True, verbose_name="Ảnh (tải lên)")
    image_url = models.URLField(blank=True, null=True, verbose_name="Ảnh (URL ngoài)")
    video_url = models.URLField(blank=True, null=True, verbose_name="Video (URL YouTube)")
    order = models.PositiveIntegerField(default=0, blank=True, verbose_name="Thứ tự")

    class Meta:
        verbose_name = "Ảnh/Video sản phẩm"
        verbose_name_plural = "Ảnh/Video sản phẩm"
        ordering = ['order']

    def display_url(self):
        if self.media_type == 'video':
            return None
        if self.image:
            return self.image.url
        return self.image_url

    def video_embed_url(self):
        if self.media_type != 'video':
            return None
        return youtube_embed_url(self.video_url)

    def __str__(self):
        return f"Media {self.pk}"


class ProductHighlight(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='highlights')
    text = models.CharField(max_length=300, verbose_name="Ý nổi bật")
    order = models.PositiveIntegerField(default=0, blank=True, verbose_name="Thứ tự")

    class Meta:
        verbose_name = "Ưu điểm vượt trội"
        verbose_name_plural = "Ưu điểm vượt trội"
        ordering = ['order']

    def __str__(self):
        return self.text


class ProductSpec(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specs')
    label = models.CharField(max_length=200, verbose_name="Tên thông số")
    value = models.CharField(max_length=300, verbose_name="Giá trị")
    order = models.PositiveIntegerField(default=0, blank=True, verbose_name="Thứ tự")

    class Meta:
        verbose_name = "Thông số sản phẩm"
        verbose_name_plural = "Thông số sản phẩm"
        ordering = ['order']

    def __str__(self):
        return f"{self.label}: {self.value}"


class NewsCategory(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Danh mục tin tức"
        verbose_name_plural = "Danh mục tin tức"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class News(models.Model):
    title = models.CharField(max_length=400, verbose_name="Tiêu đề")
    slug = models.SlugField(unique=True, blank=True, max_length=400)
    category = models.ForeignKey(NewsCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Danh mục")
    image = models.ImageField(upload_to='news/', blank=True, null=True, verbose_name="Hình ảnh")
    image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Link ảnh (URL)", help_text="Dùng khi không có sẵn file ảnh để tải lên")
    summary = models.TextField(blank=True, verbose_name="Tóm tắt")
    content = models.TextField(verbose_name="Nội dung")
    
    related_products = models.ManyToManyField('Product', blank=True, verbose_name="Sản phẩm liên quan", related_name='related_news')
    related_projects = models.ManyToManyField('Project', blank=True, verbose_name="Dự án liên quan", related_name='related_news')
    related_articles = models.ManyToManyField('self', blank=True, verbose_name="Bài viết liên quan", symmetrical=False)
    video_url = models.CharField(max_length=500, blank=True, null=True, verbose_name="URL YouTube", help_text="Dán link YouTube video phóng sự")
    author = models.CharField(max_length=200, default='Công ty TNHH Keo Vữa Sông Hồng', verbose_name="Tác giả")
    order = models.IntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    published_at = models.DateTimeField(verbose_name="Ngày đăng", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Tin tức"
        verbose_name_plural = "Tin tức"
        ordering = ['-published_at']

    def save(self, *args, **kwargs):
        if not self.slug or not self.slug.strip():
            base_slug = vietnamese_slugify(self.title) or "tin-tuc"
            slug = base_slug
            counter = 1
            while News.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        else:
            self.slug = vietnamese_slugify(self.slug)
        super().save(*args, **kwargs)

    def thumbnail_url(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        vid = self.get_video_id()
        if vid:
            return f'https://img.youtube.com/vi/{vid}/hqdefault.jpg'
        return ''

    def is_auto_video_thumbnail(self):
        """Ảnh đại diện đang lấy từ YouTube — thường có viền đen trên/dưới do letterbox 4:3."""
        if not self.image and not self.image_url and bool(self.get_video_id()):
            return True
        if self.image_url and any(domain in self.image_url for domain in ['youtube.com', 'youtu.be', 'ytimg.com']):
            return True
        return False

    def video_embed_url(self):
        return youtube_embed_url(self.video_url)

    def has_inline_video(self):
        return bool(self.content) and '<iframe' in self.content.lower()

    def get_video_id(self):
        if not self.video_url:
            return None
        url = self.video_url.strip()
        if '<iframe' in url and 'src=' in url:
            import re
            m = re.search(r'src=["\']([^"\']+)["\']', url)
            if m:
                url = m.group(1)
        if 'youtu.be/' in url:
            return url.split('youtu.be/')[-1].split('?')[0].split('&')[0]
        elif 'youtube.com/watch' in url:
            import urllib.parse
            qs = urllib.parse.urlparse(url).query
            v = urllib.parse.parse_qs(qs).get('v', [None])[0]
            return v or 'N-FLw-piwlc'
        elif 'youtube.com/shorts/' in url:
            return url.split('youtube.com/shorts/')[-1].split('?')[0].split('&')[0]
        elif 'youtube.com/embed/' in url:
            return url.split('youtube.com/embed/')[-1].split('?')[0]
        elif 'youtube-nocookie.com/embed/' in url:
            return url.split('youtube-nocookie.com/embed/')[-1].split('?')[0]
        elif len(url) == 11 and ' ' not in url and '/' not in url:
            return url
        return 'N-FLw-piwlc'

    @property
    def display_summary(self):
        source = self.summary if (self.summary and self.summary.strip()) else self.content
        return clean_html_excerpt(source, 28)

    def __str__(self):
        return self.title


class Banner(models.Model):
    title = models.CharField(max_length=300, verbose_name="Tiêu đề")
    subtitle = models.CharField(max_length=400, blank=True, verbose_name="Tiêu đề phụ")
    image = models.ImageField(upload_to='banners/', blank=True, null=True, verbose_name="Hình ảnh")
    link = models.CharField(max_length=300, blank=True, verbose_name="Đường dẫn")
    order = models.IntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Banner trang chủ"
        verbose_name_plural = "Banner trang chủ"
        ordering = ['order']

    def __str__(self):
        return self.title


class Distributor(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('headquarters', 'Địa chỉ trụ sở'),
        ('distribution_area', 'Khu vực phân phối'),
    ]

    name = models.CharField(max_length=300, verbose_name="Tên đại lý / Công ty")
    address_type = models.CharField(max_length=50, choices=ADDRESS_TYPE_CHOICES, default='headquarters', verbose_name="Loại địa chỉ")
    address = models.TextField(verbose_name="Địa chỉ / Khu vực phân phối")
    province = models.CharField(max_length=100, verbose_name="Tỉnh/Thành phố")
    hotline_label = models.CharField(max_length=100, default="HOTLINE TƯ VẤN & MUA HÀNG", blank=True, verbose_name="Tiêu đề Hotline/Liên hệ")
    phone = models.CharField(max_length=300, verbose_name="Số điện thoại / Hotline")
    map_address = models.CharField(max_length=300, blank=True, null=True, verbose_name="Địa chỉ tìm kiếm trên Google Maps")
    google_maps_link = models.TextField(blank=True, null=True, verbose_name="Link Google Maps",
        help_text="Dán link chia sẻ từ Google Maps (chứa toạ độ @lat,lng) hoặc mã nhúng iframe lấy từ Google Maps > Chia sẻ > Nhúng bản đồ. Nếu để trống, hệ thống sẽ tự tìm theo địa chỉ ở trên.")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    website = models.URLField(blank=True, null=True, verbose_name="Website")
    youtube_url = models.URLField(blank=True, null=True, verbose_name="Kênh YouTube")
    tiktok_url = models.URLField(blank=True, null=True, verbose_name="Kênh TikTok")
    order = models.IntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")

    class Meta:
        verbose_name = "Đại lý phân phối"
        verbose_name_plural = "Đại lý phân phối"
        ordering = ['province', 'name']

    def __str__(self):
        return f"{self.name} - {self.province}"


class DistributorLink(models.Model):
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE, related_name='extra_links', verbose_name="Đại lý")
    label = models.CharField(max_length=100, blank=True, verbose_name="Tên nền tảng", help_text="VD: Facebook, Zalo, Instagram...")
    url = models.URLField(max_length=500, blank=True, verbose_name="Đường dẫn")
    order = models.IntegerField(default=0, verbose_name="Thứ tự")

    class Meta:
        verbose_name = "Liên kết khác"
        verbose_name_plural = "Liên kết khác"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.label} - {self.distributor.name}"


class DealerRegistration(models.Model):
    full_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Họ tên")
    company = models.CharField(max_length=300, verbose_name="Tên doanh nghiệp/Hộ Kinh Doanh")
    tax_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Mã số thuế")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    address = models.TextField(verbose_name="Địa chỉ trụ sở")
    province = models.CharField(max_length=100, verbose_name="Khu vực đăng ký đại lý")
    products_distributed = models.TextField(blank=True, null=True, verbose_name="Sản phẩm phân phối")
    note = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False, verbose_name="Đã xử lý")

    class Meta:
        verbose_name = "Đăng ký đại lý"
        verbose_name_plural = "Đăng ký đại lý"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company} - {self.phone}"


class ProjectCategory(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên danh mục")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug")

    class Meta:
        verbose_name = "Danh mục dự án"
        verbose_name_plural = "Danh mục dự án"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


PROJECT_CATEGORY_CHOICES = [
    ('dan-dung', 'Dự án dân dụng'),
    ('cong-nghiep', 'Dự án công nghiệp'),
]

class Project(models.Model):
    title = models.CharField(max_length=400, verbose_name="Tên dự án")
    slug = models.SlugField(unique=True, blank=True, max_length=400)
    category = models.CharField(max_length=20, choices=PROJECT_CATEGORY_CHOICES, default='dan-dung', verbose_name="Loại dự án")
    client = models.CharField(max_length=300, blank=True, verbose_name="Chủ đầu tư")
    location = models.CharField(max_length=300, blank=True, verbose_name="Địa điểm")
    image = models.ImageField(upload_to='projects/', blank=True, null=True, verbose_name="Hình ảnh")
    description = models.TextField(blank=True, verbose_name="Mô tả dự án")
    products_used = models.ManyToManyField('Product', blank=True, verbose_name="Sản phẩm sử dụng")
    order = models.IntegerField(default=0, verbose_name="Thứ tự")
    is_featured = models.BooleanField(default=False, verbose_name="Dự án nổi bật")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    author = models.CharField(max_length=200, default='Công ty TNHH Keo Vữa Sông Hồng', verbose_name="Tác giả")
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Dự án"
        verbose_name_plural = "Dự án"
        ordering = ['-published_at']

    def save(self, *args, **kwargs):
        if not self.slug or not self.slug.strip():
            base_slug = vietnamese_slugify(self.title) or "du-an"
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        else:
            self.slug = vietnamese_slugify(self.slug)
        super().save(*args, **kwargs)

    @property
    def title_display(self):
        return self.title

    def get_category_display(self):
        try:
            cat = ProjectCategory.objects.filter(slug=self.category).first()
            if cat:
                return cat.name
        except Exception:
            pass
        return dict(PROJECT_CATEGORY_CHOICES).get(self.category, self.category)

    @property
    def category_display(self):
        return self.get_category_display()

    @property
    def display_description(self):
        return clean_html_excerpt(self.description, 20)

    def __str__(self):
        return self.title


class ConsultationRequest(models.Model):
    full_name = models.CharField(max_length=200, verbose_name="Họ tên")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    email = models.EmailField(blank=True, verbose_name="Email")
    company = models.CharField(max_length=300, blank=True, verbose_name="Công ty / Dự án")
    interest = models.CharField(max_length=200, blank=True, verbose_name="Quan tâm đến")
    message = models.TextField(blank=True, verbose_name="Yêu cầu cụ thể")
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False, verbose_name="Đã xử lý")

    class Meta:
        verbose_name = "Đăng ký tư vấn"
        verbose_name_plural = "Đăng ký tư vấn"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.phone}"


CATALOGUE_GROUP_CHOICES = [
    ('Hồ sơ năng lực', 'Hồ sơ năng lực'),
    ('Tài liệu vữa khô trộn sẵn', 'Tài liệu vữa khô trộn sẵn'),
    ('Tài liệu vữa dành cho gạch AAC', 'Tài liệu vữa dành cho gạch AAC'),
    ('Tài liệu keo dán gạch', 'Tài liệu keo dán gạch'),
    ('Tài liệu cát sấy khô', 'Tài liệu cát sấy khô'),
]

class Catalogue(models.Model):
    title = models.CharField(max_length=400, verbose_name="Tiêu đề catalogue")
    slug = models.SlugField(unique=True, blank=True, max_length=400)
    category = models.CharField(max_length=50, blank=True, default='', verbose_name="Loại catalogue")
    group_name = models.CharField(max_length=255, choices=CATALOGUE_GROUP_CHOICES, default='Hồ sơ năng lực', verbose_name="Tên nhóm tài liệu")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    thumbnail = models.ImageField(upload_to='catalogues/', blank=True, null=True, verbose_name="Ảnh bìa")
    file = models.FileField(upload_to='catalogues/files/', blank=True, null=True, verbose_name="File PDF")
    order = models.IntegerField(default=0, verbose_name="Số thứ tự sắp xếp")
    related_products = models.ManyToManyField('Product', blank=True, verbose_name="Sản phẩm liên quan", related_name='related_catalogues')
    related_projects = models.ManyToManyField('Project', blank=True, verbose_name="Dự án liên quan", related_name='related_catalogues')
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "E-Catalog"
        verbose_name_plural = "E-Catalog"
        ordering = ['group_name', 'order', 'title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Luôn tự động tạo/trích xuất ảnh bìa thumbnail từ file được tải lên (hỗ trợ cả PDF và Ảnh JPG/PNG)
        if self.file:
            file_name = self.file.name.lower()
            if any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                try:
                    import io
                    from django.core.files.base import ContentFile
                    from django.utils import timezone
                    self.file.seek(0)
                    img_bytes = self.file.read()
                    self.file.seek(0)
                    if img_bytes:
                        thumb_name = f"cat_thumb_{self.slug or 'cover'}_{int(timezone.now().timestamp())}.jpg"
                        self.thumbnail.save(thumb_name, ContentFile(img_bytes), save=False)
                except Exception:
                    pass
            else:
                try:
                    import io
                    import pypdfium2 as pdfium
                    from django.core.files.base import ContentFile
                    from django.utils import timezone
                    self.file.seek(0)
                    pdf_bytes = self.file.read()
                    self.file.seek(0)
                    if pdf_bytes:
                        pdf = pdfium.PdfDocument(pdf_bytes)
                        if len(pdf) > 0:
                            page = pdf[0]
                            img = page.render(scale=2).to_pil()
                            # Nếu trang 1 PDF là dạng trải 2 trang (landscape), tự động lấy nửa phải làm trang bìa trước
                            if img.width > img.height * 1.2:
                                img = img.crop((img.width // 2, 0, img.width, img.height))
                            buf = io.BytesIO()
                            img.save(buf, format='JPEG', quality=90)
                            thumb_name = f"cat_thumb_{self.slug or 'cover'}_{int(timezone.now().timestamp())}.jpg"
                            self.thumbnail.save(thumb_name, ContentFile(buf.getvalue()), save=False)
                except Exception:
                    pass
        else:
            if not self.file:
                self.thumbnail = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    full_name = models.CharField(max_length=200, verbose_name="Họ tên")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    email = models.EmailField(blank=True, verbose_name="Email")
    message = models.TextField(verbose_name="Nội dung")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tin nhắn liên hệ"
        verbose_name_plural = "Tin nhắn liên hệ"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.phone}"


class ThemeSettings(models.Model):
    # ── 1. ĐẦU TRANG & LOGO ──
    logo = models.ImageField(upload_to='theme/', blank=True, null=True, verbose_name="Logo công ty")
    header_text = models.CharField(max_length=255, blank=True, null=True, verbose_name="Slogan / Thông báo đầu trang")
    show_megamenu = models.BooleanField(default=False, verbose_name="Hiển thị megamenu")
    hotline_1 = models.CharField(max_length=50, blank=True, null=True, verbose_name="Hotline 1")
    hotline_2 = models.CharField(max_length=50, blank=True, null=True, verbose_name="Hotline 2")
    email = models.EmailField(blank=True, null=True, verbose_name="Email liên hệ")
    open_hours = models.CharField(max_length=100, blank=True, null=True, verbose_name="Giờ mở cửa")
    cta_btn_text = models.CharField(max_length=100, default="ĐĂNG KÝ ĐẠI LÝ", blank=True, verbose_name="Chữ trên nút CTA Header")
    cta_btn_link = models.CharField(max_length=255, default="/dang-ky-dai-ly/", blank=True, verbose_name="Đường dẫn nút CTA Header")

    # ── BANNER HERO ĐẦU TRANG CHỦ ──
    hero_title = models.CharField(max_length=255, default="Công ty TNHH Keo Vữa Sông Hồng", blank=True, verbose_name="Tiêu đề Banner chính")
    hero_desc = models.TextField(default="Nhà máy sản xuất vữa khô trộn sẵn, keo dán gạch chất lượng cao", blank=True, verbose_name="Mô tả Banner chính")
    hero_btn_text = models.CharField(max_length=100, default="Khám Phá Sản Phẩm", blank=True, verbose_name="Chữ trên nút Banner")
    hero_btn_link = models.CharField(max_length=255, default="/san-pham/#plStickyNav", blank=True, verbose_name="Đường dẫn nút Banner")
    hero_video_file = models.FileField(upload_to='theme/videos/', blank=True, null=True, verbose_name="Tải file Video Banner lên (.mp4)")
    hero_video_url = models.CharField(max_length=500, blank=True, null=True, verbose_name="Hoặc dán đường dẫn Video nền MP4")

    # ── 2. TRANG CHỦ - MODULE GIỚI THIỆU ──
    show_intro = models.BooleanField(default=True, verbose_name="Hiển thị Module Giới thiệu")
    intro_badge = models.CharField(max_length=100, default="Giới thiệu", blank=True, verbose_name="Thẻ phụ (Badge)")
    intro_title = models.CharField(max_length=255, default="Về chúng tôi", blank=True, verbose_name="Tiêu đề giới thiệu")
    intro_description = models.TextField(
        default="""Công ty TNHH Keo Vữa Sông Hồng là đơn vị hoạt động trong lĩnh vực sản xuất vật liệu xây dựng tại Hưng Yên. Với kinh nghiệm trong ngành cùng hệ thống dây chuyền, máy móc và công nghệ hiện đại, chúng tôi tập trung nghiên cứu và sản xuất những sản phẩm đáp ứng yêu cầu ngày càng cao của thị trường.

Không chỉ tạo ra vật liệu mới, SHK Mortar hướng tới những giải pháp phù hợp với phương thức xây dựng hiện đại – nơi chất lượng, tính ổn định và hiệu quả thi công được đặt lên hàng đầu. Mỗi sản phẩm được nghiên cứu, kiểm soát và kiểm định chặt chẽ, nhằm tạo ra giá trị thiết thực cho công trình và đối tác.

Với định hướng đưa các sản phẩm chất lượng đến gần hơn với thị trường, từ dự án đến công trình dân dụng, SHK Mortar từng bước phát triển hệ giải pháp vật liệu giúp tối ưu quy trình thi công và chi phí, hướng tới một phương thức xây dựng hiệu quả hơn và tạo nên một cách tiếp cận mới cho ngành xây dựng.""",
        blank=True,
        null=True,
        verbose_name="Nội dung giới thiệu (HTML/Văn bản)"
    )
    intro_youtube_url = models.CharField(
        max_length=500,
        default="https://www.youtube.com/watch?v=N-FLw-piwlc",
        blank=True,
        null=True,
        verbose_name="Link YouTube video giới thiệu"
    )

    # ── 3. TRANG CHỦ - DANH MỤC SẢN PHẨM ──
    show_products = models.BooleanField(default=True, verbose_name="Hiển thị Module Danh mục sản phẩm")
    products_badge = models.CharField(max_length=100, default="Khám phá", blank=True, verbose_name="Thẻ phụ (Badge)")
    products_title = models.CharField(max_length=255, default="Danh mục sản phẩm", blank=True, verbose_name="Tiêu đề Danh mục sản phẩm")
    products_btn_text = models.CharField(max_length=100, default="Xem tất cả sản phẩm", blank=True, verbose_name="Chữ trên nút xem tất cả")
    products_btn_link = models.CharField(max_length=255, default="/san-pham/#plStickyNav", blank=True, verbose_name="Đường dẫn nút xem tất cả")

    # 4 ô danh mục sản phẩm nổi bật trên trang chủ
    prod_cat_1_title = models.CharField(max_length=255, default="Vữa khô trộn sẵn", blank=True, verbose_name="Tên danh mục 1")
    prod_cat_1_link = models.CharField(max_length=255, default="/san-pham/#cat-vua-kho-tron-san", blank=True, verbose_name="Đường dẫn danh mục 1")
    prod_cat_1_image = models.ImageField(upload_to='theme/products/', blank=True, null=True, verbose_name="Ảnh danh mục 1")

    prod_cat_2_title = models.CharField(max_length=255, default="Vữa xây trát AAC", blank=True, verbose_name="Tên danh mục 2")
    prod_cat_2_link = models.CharField(max_length=255, default="/san-pham/#cat-vua-xay-trat-aac", blank=True, verbose_name="Đường dẫn danh mục 2")
    prod_cat_2_image = models.ImageField(upload_to='theme/products/', blank=True, null=True, verbose_name="Ảnh danh mục 2")

    prod_cat_3_title = models.CharField(max_length=255, default="Keo dán gạch", blank=True, verbose_name="Tên danh mục 3")
    prod_cat_3_link = models.CharField(max_length=255, default="/san-pham/#cat-keo-dan-gach-da", blank=True, verbose_name="Đường dẫn danh mục 3")
    prod_cat_3_image = models.ImageField(upload_to='theme/products/', blank=True, null=True, verbose_name="Ảnh danh mục 3")

    prod_cat_4_title = models.CharField(max_length=255, default="Cát sấy khô", blank=True, verbose_name="Tên danh mục 4")
    prod_cat_4_link = models.CharField(max_length=255, default="/san-pham/#cat-cat-sach-say-kho", blank=True, verbose_name="Đường dẫn danh mục 4")
    prod_cat_4_image = models.ImageField(upload_to='theme/products/', blank=True, null=True, verbose_name="Ảnh danh mục 4")

    # ── 4. TRANG CHỦ - PHÓNG SỰ THỰC TẾ ──
    show_phong_su = models.BooleanField(default=True, verbose_name="Hiển thị Module Phóng sự thực tế")
    phong_su_badge = models.CharField(max_length=100, default="Xem thêm", blank=True, verbose_name="Thẻ phụ phóng sự")
    phong_su_title = models.CharField(max_length=255, default="Phóng sự thực tế", blank=True, verbose_name="Tiêu đề phóng sự")
    phong_su_desc = models.TextField(
        default="Theo sát những công trình thực tế, ghi nhận câu chuyện và trải nghiệm từ thợ thi công, đại lý, nhà thầu và chủ đầu tư. Qua đó, thương hiệu giới thiệu chất lượng sản phẩm, giải pháp thi công và dấu ấn đồng hành trên từng công trình.",
        blank=True,
        null=True,
        verbose_name="Mô tả phóng sự thực tế"
    )
    phong_su_btn_text = models.CharField(max_length=100, default="XEM TẤT CẢ", blank=True, verbose_name="Chữ trên nút phóng sự")
    phong_su_btn_link = models.CharField(max_length=255, default="/tin-tuc/?category=phong-su-thuc-te", blank=True, verbose_name="Đường dẫn nút phóng sự")

    # ── 4. TRANG CHỦ - MINH CHỨNG CHẤT LƯỢNG ──
    show_quality = models.BooleanField(default=True, verbose_name="Hiển thị Module Minh chứng chất lượng")
    quality_image = models.ImageField(upload_to='theme/quality/', blank=True, null=True, verbose_name="Thêm ảnh chứng nhận mới vào Slider")
    quality_title = models.CharField(max_length=255, default="Minh chứng chất lượng", blank=True, verbose_name="Tiêu đề minh chứng chất lượng")
    quality_description_html = models.TextField(
        default="""SHK Mortar áp dụng hệ thống quản lý và kiểm soát chất lượng nghiêm ngặt, được kiểm định bởi các đơn vị chuyên môn.

Sản phẩm đáp ứng các tiêu chuẩn:
- ISO 9001:2015 (Hệ thống quản lý chất lượng QMS)
- TCVN 4314:2022 (Tiêu chuẩn Vữa xây dựng)
- TCVN 7899-1:2008 (Tiêu chuẩn Keo dán gạch)
- TCVN 9028:2011 (Tiêu chuẩn Vữa cho bê tông nhẹ)

cùng các chứng nhận và hồ sơ kiểm tra chất lượng liên quan, đảm bảo tính ổn định và tin cậy trong từng công trình.""",
        blank=True,
        null=True,
        verbose_name="Nội dung tiêu chuẩn chất lượng (Văn bản)"
    )
    quality_drive_link = models.CharField(
        max_length=500,
        default="https://drive.google.com/drive/folders/1-2VEnOxoTh2CG0laK1VURFiEDBvzOOQd?hl=vi",
        blank=True,
        null=True,
        verbose_name="Đường dẫn Google Drive (Hồ sơ kiểm nghiệm)"
    )
    quality_drive_btn_text = models.CharField(max_length=100, default="Tải Giấy Kiểm Nghiệm", blank=True, verbose_name="Chữ trên nút tải chứng nhận")

    # ── 5. CHÂN TRANG (FOOTER) ──
    footer_company_name = models.CharField(max_length=255, default="Công ty TNHH Keo Vữa Sông Hồng", blank=True, verbose_name="Tên công ty Footer")
    footer_address = models.CharField(max_length=255, default="Thôn Ninh Tập, xã Châu Ninh, Hưng Yên", blank=True, null=True, verbose_name="Địa chỉ nhà máy")
    footer_office_address = models.CharField(max_length=255, default="Vinhomes Ocean Park 2, Văn Giang, Hưng Yên", blank=True, verbose_name="Địa chỉ văn phòng")
    footer_phone = models.CharField(max_length=50, default="0938016788", blank=True, null=True, verbose_name="SĐT footer")
    footer_email = models.EmailField(default="kinhdoanh@keovuasonghong.vn", blank=True, null=True, verbose_name="Email phòng kinh doanh")
    footer_media_email = models.EmailField(default="admin@keovuasonghong.vn", blank=True, verbose_name="Email hợp tác truyền thông")
    footer_info_html = models.TextField(blank=True, null=True, verbose_name="Nội dung tuỳ chỉnh cột công ty (HTML)")

    # Cột tài liệu tham khảo
    footer_doc_1_title = models.CharField(max_length=150, default="Chính sách và Điều khoản", blank=True, verbose_name="Tên tài liệu 1")
    footer_doc_1_link = models.CharField(max_length=255, default="/chinh-sach-va-dieu-khoan/", blank=True, verbose_name="Đường dẫn tài liệu 1")
    footer_doc_2_title = models.CharField(max_length=150, default="", blank=True, verbose_name="Tên tài liệu 2")
    footer_doc_2_link = models.CharField(max_length=255, default="", blank=True, verbose_name="Đường dẫn tài liệu 2")
    footer_doc_3_title = models.CharField(max_length=150, default="Hồ Sơ Năng Lực", blank=True, verbose_name="Tên tài liệu 3")
    footer_doc_3_link = models.CharField(max_length=255, default="/e-catalog/?doc=ho-so-nang-luc", blank=True, verbose_name="Đường dẫn tài liệu 3")
    footer_doc_4_title = models.CharField(max_length=150, default="Hồ Sơ Kỹ Thuật", blank=True, verbose_name="Tên tài liệu 4")
    footer_doc_4_link = models.CharField(max_length=255, default="/e-catalog/", blank=True, verbose_name="Đường dẫn tài liệu 4")

    # Mạng xã hội & liên kết
    footer_group = models.URLField(default="https://www.facebook.com/groups/4105613262904191", blank=True, null=True, verbose_name="Link Group Facebook")
    footer_facebook = models.URLField(default="https://www.facebook.com/keovuasonghong.vn/", blank=True, null=True, verbose_name="Link Facebook Fanpage")
    footer_zalo = models.URLField(default="https://zalo.me/3423135266242009757", blank=True, null=True, verbose_name="Link Zalo OA")
    footer_youtube = models.URLField(default="https://www.youtube.com/@keovuasonghong", blank=True, null=True, verbose_name="Link YouTube")
    footer_tiktok = models.URLField(default="https://www.tiktok.com/@shkmortar", blank=True, null=True, verbose_name="Link TikTok")
    footer_linkedin = models.URLField(default="https://www.linkedin.com", blank=True, null=True, verbose_name="Link LinkedIn")
    footer_shopee = models.URLField(default="https://shopee.vn/shop/1658539442", blank=True, null=True, verbose_name="Link Shopee")
    footer_map_iframe = models.TextField(default='<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3730.0519155167885!2d105.9292376!3d20.7891875!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3135b7ebaf798ae9%3A0x12abc2f8114a7f71!2sNh%C3%A0%20m%C3%A1y%20Keo%20V%E1%BB%AFa%20S%C3%B4ng%20H%E1%BB%93ng%20-%20SHK%20Mortar!5e0!3m2!1svi!2svn!4v1700000000000!5m2!1svi!2svn" title="Nhà máy Keo Vữa Sông Hồng - SHK Mortar" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>', blank=True, null=True, verbose_name="Mã nhúng iframe Google Maps")
    footer_copyright = models.CharField(max_length=255, default="© 2026. Mọi bản quyền được bảo lưu bởi Công ty TNHH Keo Vữa Sông Hồng", blank=True, verbose_name="Bản quyền Footer")

    # ── 6. TRANG GIỚI THIỆU (VỀ CHÚNG TÔI) ──
    about_hero_title = models.CharField(max_length=255, default="Về chúng tôi", blank=True, verbose_name="Tiêu đề Banner Đầu trang")
    about_intro_image = models.ImageField(upload_to='theme/about/', blank=True, null=True, verbose_name="Ảnh giới thiệu chung")
    about_main_heading = models.CharField(max_length=255, default="Giới thiệu Công ty TNHH Keo Vữa Sông Hồng", blank=True, verbose_name="Tiêu đề chính giới thiệu")
    about_intro_content = models.TextField(
        default="""Công ty TNHH Keo Vữa Sông Hồng (SHK Mortar) được thành lập năm 2025, hoạt động trong lĩnh vực sản xuất và phân phối vật liệu xây dựng, với nhà máy đầu tiên đặt tại Hưng Yên, có quy mô hơn 3.000 m².

Nhà máy được đầu tư máy móc hiện đại, hệ thống sản xuất bán tự động và quy trình vận hành bài bản, với hai dây chuyền chuyên sản xuất vữa khô trộn sẵn, keo dán gạch và cát tự nhiên sấy khô, đáp ứng đa dạng nhu cầu của thị trường.

Sở hữu đội ngũ giàu kinh nghiệm và am hiểu thực tiễn ngành vật liệu xây dựng, SHK Mortar chú trọng kiểm soát chất lượng từ nguồn nguyên liệu đầu vào đến quá trình sản xuất, nhằm tạo ra những sản phẩm ổn định, chất lượng và phù hợp với yêu cầu thi công.

Với lợi thế về vị trí nhà máy, nguồn nguyên vật liệu dồi dào và năng lực sản xuất, Keo Vữa Sông Hồng hướng tới xây dựng hệ thống cung ứng vật liệu xây dựng chất lượng, vận chuyển nhanh chóng và dịch vụ hậu mãi chuyên nghiệp, trở thành đối tác tin cậy của khách hàng và các đơn vị thi công.""",
        blank=True,
        verbose_name="Nội dung các đoạn văn giới thiệu"
    )

    # Thông điệp & Năng lực
    about_statement_heading = models.CharField(max_length=255, default="Sự khởi nguồn của mọi công trình bền vững", blank=True, verbose_name="Tiêu đề Thông điệp")
    about_statement_col1 = models.TextField(
        default="""Chúng tôi mang đến hệ sản phẩm vật liệu xây dựng tối ưu cho thi công, giúp người thợ đơn giản hóa quy trình, tiết kiệm thời gian và nâng cao hiệu quả công việc. Thay thế những hạn chế của phương pháp truyền thống bằng các giải pháp vật liệu hiện đại, ổn định và phù hợp với yêu cầu ngày càng cao của công trình.""",
        blank=True,
        verbose_name="Thông điệp - Cột trái"
    )
    about_statement_col2 = models.TextField(
        default="""Đồng thời không ngừng mở rộng và đồng hành cùng hệ thống đại lý, kết nối sâu hơn với các đội thợ và nhà thầu từ quy mô vừa đến nhỏ. Bằng việc đưa giải pháp vật liệu chất lượng đến từng công trình, từng ngôi nhà, góp phần kiến tạo hàng vạn công trình bền vững, hiện thực hóa sứ mệnh "Khởi nguồn cho hàng vạn công trình bền vững".""",
        blank=True,
        verbose_name="Thông điệp - Cột phải"
    )

    # Câu chuyện thương hiệu
    about_story_heading = models.CharField(max_length=255, default="Câu chuyện thương hiệu", blank=True, verbose_name="Tiêu đề Câu chuyện thương hiệu")
    about_story_content = models.TextField(
        default="""SHK Mortar ra đời từ mong muốn giúp người thợ thi công hiệu quả hơn — nhanh hơn, tiết kiệm hơn và bền vững hơn. Từ hành trình nghiên cứu, hoàn thiện công thức phối trộn đến đồng hành cùng đại lý, đội thợ và nhà thầu, chúng tôi tạo ra những giải pháp vật liệu phù hợp với thực tế, góp phần kiến tạo những công trình trọn vẹn và bền vững.""",
        blank=True,
        verbose_name="Nội dung Câu chuyện thương hiệu"
    )
    about_story_image = models.ImageField(upload_to='theme/about/', blank=True, null=True, verbose_name="Ảnh Câu chuyện thương hiệu")

    # Tầm nhìn & Cam kết
    about_vision_title = models.CharField(max_length=255, default="Tầm nhìn", blank=True, verbose_name="Tiêu đề Tầm nhìn")
    about_vision_desc = models.TextField(
        default="""Trở thành thương hiệu vữa khô trộn sẵn và keo dán gạch hàng đầu trên thị trường, mở rộng hệ thống phân phối đại lý tới khắp các tỉnh thành tại Việt Nam.""",
        blank=True,
        verbose_name="Nội dung Tầm nhìn"
    )
    about_commitment_title = models.CharField(max_length=255, default="Cam kết của chúng tôi", blank=True, verbose_name="Tiêu đề Cam kết")
    about_commitment_desc = models.TextField(
        default="""SHK Mortar cam kết cung cấp sản phẩm chất lượng, tối ưu chi phí và dịch vụ chu đáo; chúng tôi lấy khách hàng làm trọng tâm của mọi sự phát triển, liên tục cập nhật và chuyển mình để phù hợp với nhu cầu của khách hàng mục tiêu.""",
        blank=True,
        verbose_name="Nội dung Cam kết"
    )

    # Thư viện ảnh
    about_gallery_title = models.CharField(max_length=255, default="Thư viện ảnh SHK", blank=True, verbose_name="Tiêu đề Thư viện ảnh")

    class Meta:
        verbose_name = "Cài đặt Giao diện & Logo"
        verbose_name_plural = "Cài đặt Giao diện & Logo"

    def clean(self):
        super().clean()
        if self.intro_youtube_url:
            u = self.intro_youtube_url.strip()
            if '<iframe' in u and 'src=' in u:
                import re
                m = re.search(r'src=["\']([^"\']+)["\']', u)
                if m:
                    u = m.group(1)
            if u and not u.startswith(('http://', 'https://')) and not u.startswith('<'):
                if 'youtube.com' in u or 'youtu.be' in u:
                    u = 'https://' + u
            self.intro_youtube_url = u

    def save(self, *args, **kwargs):
        self.pk = 1
        if self.intro_youtube_url:
            u = self.intro_youtube_url.strip()
            if '<iframe' in u and 'src=' in u:
                import re
                m = re.search(r'src=["\']([^"\']+)["\']', u)
                if m:
                    u = m.group(1)
            if u and not u.startswith(('http://', 'https://')) and not u.startswith('<'):
                if 'youtube.com' in u or 'youtu.be' in u:
                    u = 'https://' + u
            self.intro_youtube_url = u
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def intro_embed_url(self):
        return youtube_embed_url(self.intro_youtube_url)

    def hero_youtube_id(self):
        if not self.hero_video_url:
            return None
        url = self.hero_video_url.strip()
        if 'youtu.be/' in url:
            return url.split('youtu.be/')[-1].split('?')[0].split('&')[0]
        elif 'youtube.com/watch' in url:
            import urllib.parse
            qs = urllib.parse.urlparse(url).query
            return urllib.parse.parse_qs(qs).get('v', [None])[0]
        elif 'youtube.com/shorts/' in url:
            return url.split('youtube.com/shorts/')[-1].split('?')[0].split('&')[0]
        elif 'youtube.com/embed/' in url:
            return url.split('youtube.com/embed/')[-1].split('?')[0].split('&')[0]
        return None

    def hero_youtube_embed_url(self):
        vid = self.hero_youtube_id()
        if vid:
            return f"https://www.youtube.com/embed/{vid}?autoplay=1&mute=1&loop=1&playlist={vid}&controls=0&showinfo=0&rel=0&playsinline=1&enablejsapi=1"
        return None

    @property
    def is_hero_youtube(self):
        return bool(self.hero_youtube_id())

    @property
    def quality_description_rendered(self):
        if not self.quality_description_html:
            return ""
        text = self.quality_description_html.strip()
        if '<p' in text or '<ul' in text or '<div' in text:
            return text
        lines = [line.strip() for line in text.splitlines()]
        output, in_list, p_buffer = [], False, []
        def flush_p():
            nonlocal p_buffer
            if p_buffer:
                output.append(f'<p class="about-para">{" ".join(p_buffer)}</p>')
                p_buffer = []
        def flush_list():
            nonlocal in_list
            if in_list:
                output.append('</ul>')
                in_list = False
        for line in lines:
            if not line:
                flush_p()
                flush_list()
            elif line.startswith(('-', '•', '*')):
                flush_p()
                if not in_list:
                    output.append('<ul class="quality-bullet-list">')
                    in_list = True
                bullet_content = line.lstrip('-•* ').strip()
                output.append(f'<li>{bullet_content}</li>')
            else:
                flush_list()
                p_buffer.append(line)
        flush_p()
        flush_list()
        return '\n'.join(output)

    def __str__(self):
        return "Tùy chỉnh giao diện website"


class HomeBanner(models.Model):
    theme = models.ForeignKey(ThemeSettings, on_delete=models.CASCADE, related_name='banners')
    image = models.ImageField(upload_to='banners/', verbose_name="Hình ảnh banner")
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tiêu đề")
    link = models.URLField(blank=True, null=True, verbose_name="Link liên kết")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")

    class Meta:
        verbose_name = "Banner Trang chủ"
        verbose_name_plural = "Banners Trang chủ"
        ordering = ['order']

    def __str__(self):
        return self.title or f"Banner {self.pk}"


class Partner(models.Model):
    theme = models.ForeignKey(ThemeSettings, on_delete=models.CASCADE, related_name='partners')
    image = models.ImageField(upload_to='partners/', verbose_name="Logo đối tác")
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tên đối tác")
    link = models.URLField(blank=True, null=True, verbose_name="Link liên kết")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")

    class Meta:
        verbose_name = "Đối tác"
        verbose_name_plural = "Đối tác"
        ordering = ['order']

    def __str__(self):
        return self.name or f"Đối tác {self.pk}"


class AboutGalleryImage(models.Model):
    RATIO_CHOICES = [
        ('square', 'Vuông'),
        ('tall', 'Đứng cao'),
        ('big-tall', 'Đứng rất cao'),
        ('portrait', 'Đứng vừa'),
        ('landscape', 'Ngang'),
        ('pano', 'Ngang hẹp'),
        ('small', 'Nhỏ'),
    ]
    theme = models.ForeignKey(ThemeSettings, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='theme/about_gallery/', blank=True, null=True, verbose_name="Ảnh (tải lên)")
    image_url = models.URLField(blank=True, null=True, verbose_name="Ảnh (URL ngoài)")
    caption = models.CharField(max_length=255, blank=True, verbose_name="Chú thích")
    ratio = models.CharField(max_length=20, choices=RATIO_CHOICES, default='square', verbose_name="Tỉ lệ khung ảnh")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")

    class Meta:
        verbose_name = "Ảnh Thư viện (Giới thiệu)"
        verbose_name_plural = "Ảnh Thư viện (Giới thiệu)"
        ordering = ['order']

    def display_url(self):
        if self.image:
            return self.image.url
        return self.image_url or ''

    def __str__(self):
        return self.caption or f"Ảnh {self.pk}"


class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, default="Công ty TNHH Keo Vữa Sông Hồng", verbose_name="Họ và tên")
    phone = models.CharField(max_length=50, default="0938016788", blank=True, verbose_name="Số điện thoại")
    email = models.EmailField(default="admin@keovuasonghong.vn", blank=True, verbose_name="Email")
    birthday = models.DateField(null=True, blank=True, verbose_name="Ngày sinh")
    gender = models.CharField(max_length=20, default="Nam", choices=[('Nam', 'Nam'), ('Nữ', 'Nữ'), ('Khác', 'Khác')], verbose_name="Giới tính")
    region = models.CharField(max_length=255, default="Hưng Yên - Huyện Khoái Châu", blank=True, verbose_name="Khu vực")
    ward = models.CharField(max_length=255, default="Xã Đông Ninh", blank=True, verbose_name="Phường/Xã")
    address = models.CharField(max_length=255, blank=True, verbose_name="Địa chỉ")

    class Meta:
        verbose_name = "Hồ sơ tài khoản"
        verbose_name_plural = "Hồ sơ tài khoản"

    @classmethod
    def get_for_user(cls, user):
        obj, _ = cls.objects.get_or_create(
            user=user,
            defaults={
                'full_name': user.get_full_name() or "Công ty TNHH Keo Vữa Sông Hồng",
                'email': user.email or "admin@keovuasonghong.vn",
                'phone': "0938016788",
                'region': "Hưng Yên - Huyện Khoái Châu",
                'ward': "Xã Đông Ninh",
            }
        )
        return obj

    def __str__(self):
        return f"Hồ sơ {self.user.username}"

