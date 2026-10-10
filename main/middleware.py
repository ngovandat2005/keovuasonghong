import re
from django.http import HttpResponsePermanentRedirect
from .legacy_redirects import LEGACY_URL_MAPPING


class LegacyRedirectMiddleware:
    """
    Tự động chuyển hướng (301 Permanent Redirect) các URL cũ từ web Sapo
    về cấu trúc URL mới của website Keo Vữa Sông Hồng.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        
        # Bỏ qua các URL admin, static, media
        if path.startswith(('/admin/', '/static/', '/media/')):
            return self.get_response(request)

        # Chuẩn hoá slug: bỏ slash đầu và cuối, bỏ đuôi .html nếu có
        slug = path.strip('/')
        if slug.endswith('.html'):
            slug = slug[:-5]

        if slug:
            # Bảng mapping URL cũ (Sapo) -> URL mới. Bài viết/sản phẩm/dự án giờ dùng URL gọn /<slug>/
            # nên đích dạng /tin-tuc|san-pham|du-an/<danh-muc>/<slug>/ được rút gọn thành /<slug>/.
            target_url = LEGACY_URL_MAPPING.get(slug)
            if target_url:
                m = re.match(r'^/(?:tin-tuc|san-pham|du-an)/[^/]+/([^/]+)/$', target_url)
                if m:
                    target_url = f'/{m.group(1)}/'
                # Đích trùng chính đường dẫn đang truy cập thì để view xử lý (tránh vòng lặp chuyển hướng)
                if target_url.strip('/') != slug:
                    query_string = request.META.get('QUERY_STRING')
                    if query_string:
                        target_url = f"{target_url}?{query_string}"
                    return HttpResponsePermanentRedirect(target_url)

        return self.get_response(request)


class NonWwwRedirectMiddleware:
    """
    Chuyển hướng 301 từ www.keovuasonghong.vn về keovuasonghong.vn (giữ nguyên đường dẫn và query).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        if host.lower().startswith('www.'):
            target = f'https://{host[4:]}{request.get_full_path()}'
            return HttpResponsePermanentRedirect(target)
        return self.get_response(request)
