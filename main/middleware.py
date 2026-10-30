import re
from django.http import HttpResponsePermanentRedirect
from .legacy_redirects import LEGACY_URL_MAPPING


_SKIP_PREFIXES = ('/admin/', '/static/', '/media/')
_SHORTEN_RE = re.compile(r'^/(?:tin-tuc|san-pham|du-an)/[^/]+/([^/]+)/$')


def short_url_for(path):
    """
    Trả về URL gọn đích (/<slug>/) nếu `path` là URL cũ cần chuyển hướng, ngược lại trả None.
    Dùng chung cho cả LegacyRedirectMiddleware và NonWwwRedirectMiddleware để mọi trường hợp
    chỉ qua đúng 1 lần 301 (tránh chuỗi www -> non-www -> URL gọn).
    """
    if path.startswith(_SKIP_PREFIXES):
        return None

    # Chuẩn hoá slug: bỏ slash đầu và cuối, bỏ đuôi .html nếu có
    slug = path.strip('/')
    if slug.endswith('.html'):
        slug = slug[:-5]
    if not slug:
        return None

    # Bảng mapping URL cũ (Sapo) -> URL mới. Bài viết/sản phẩm/dự án giờ dùng URL gọn /<slug>/
    # nên đích dạng /tin-tuc|san-pham|du-an/<danh-muc>/<slug>/ được rút gọn thành /<slug>/.
    target_url = LEGACY_URL_MAPPING.get(slug)
    if target_url:
        m = _SHORTEN_RE.match(target_url)
        if m:
            target_url = f'/{m.group(1)}/'
        # Đích trùng chính đường dẫn đang truy cập thì để view xử lý (tránh vòng lặp chuyển hướng).
        # So với `path` (không phải slug) để /<slug>.html và /<slug> cũng được chuyển về /<slug>/ ngay 1 bước.
        if target_url != path:
            return target_url
        return None

    # URL dạng /tin-tuc|san-pham|du-an/<danh-muc>/<slug>/ -> /<slug>/ (chỉ khi nội dung còn tồn tại,
    # nếu không để view trả 404 như cũ)
    m = _SHORTEN_RE.match(path)
    if m:
        from .models import News, Product, Project
        short_slug = m.group(1)
        for model in (Project, Product, News):
            if model.objects.filter(slug=short_slug, is_active=True).exists():
                return f'/{short_slug}/'
    return None


class LegacyRedirectMiddleware:
    """
    Tự động chuyển hướng (301 Permanent Redirect) các URL cũ từ web Sapo
    về cấu trúc URL mới của website Keo Vữa Sông Hồng.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        target_url = short_url_for(request.path)
        if target_url:
            query_string = request.META.get('QUERY_STRING')
            if query_string:
                target_url = f"{target_url}?{query_string}"
            return HttpResponsePermanentRedirect(target_url)

        return self.get_response(request)


class NonWwwRedirectMiddleware:
    """
    Chuyển hướng 301 từ www.keovuasonghong.vn về keovuasonghong.vn (giữ nguyên đường dẫn và query).
    Nếu đường dẫn còn là URL cũ thì chuyển thẳng tới URL gọn trong cùng 1 lần 301.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        if host.lower().startswith('www.'):
            path = short_url_for(request.path) or request.path
            query_string = request.META.get('QUERY_STRING')
            target = f'https://{host[4:]}{path}' + (f'?{query_string}' if query_string else '')
            return HttpResponsePermanentRedirect(target)
        return self.get_response(request)
