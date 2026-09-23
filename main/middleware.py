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
            target_url = None
            
            # 1. Ưu tiên kiểm tra xem có bài viết News nào trùng slug không
            try:
                from main.models import News
                news_item = News.objects.filter(slug=slug, is_active=True).select_related('category').first()
                if news_item:
                    cat_slug = news_item.category.slug if news_item.category else 'tin-tuc'
                    target_url = f'/tin-tuc/{cat_slug}/{news_item.slug}/'
            except Exception:
                pass

            # 2. Nếu chưa có bài viết riêng, lấy URL từ bảng mapping dự phòng
            if not target_url:
                target_url = LEGACY_URL_MAPPING.get(slug)

            if target_url:
                query_string = request.META.get('QUERY_STRING')
                if query_string:
                    target_url = f"{target_url}?{query_string}"
                return HttpResponsePermanentRedirect(target_url)

        return self.get_response(request)
