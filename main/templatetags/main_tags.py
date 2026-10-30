import html
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='clean_text')
def clean_text(value):
    """
    Decodes HTML entities (e.g., &ocirc; -> ô, &nbsp; -> space), strips HTML tags,
    and normalizes whitespace.
    """
    if not value:
        return ""
    text = str(value)
    # Double unescape in case of double-escaped entities like &amp;ocirc;
    text = html.unescape(text)
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('\xa0', ' ').replace('&nbsp;', ' ')
    return ' '.join(text.split())


@register.simple_tag(takes_context=True)
def absolute_url(context, url):
    """
    Trả về URL tuyệt đối (https://domain/...) cho thẻ Open Graph — Facebook/Zalo
    không nhận đường dẫn tương đối như /media/... khi lấy ảnh xem trước.
    """
    if not url:
        return ""
    url = str(url)
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith(('http://', 'https://')):
        return url
    request = context.get('request')
    if request is None:
        return url
    if not url.startswith('/'):
        url = '/' + url
    return f"https://{request.get_host()}{url}"


@register.filter(name='clean_excerpt')
def clean_excerpt(value, max_words=28):
    """
    Cleans text from HTML tags and entities, then truncates to max_words.
    """
    cleaned = clean_text(value)
    if not cleaned:
        return ""
    try:
        max_words = int(max_words)
    except (ValueError, TypeError):
        max_words = 28
    words = cleaned.split()
    if len(words) > max_words:
        return ' '.join(words[:max_words]) + '...'
    return cleaned


@register.filter(name='tach_sdt')
def tach_sdt(value):
    """Tách ô nhiều số điện thoại ("0938016788 - 0386360797") thành list từng số.
    Phân cách: dấu - (chuẩn), và vẫn nhận dấu phẩy / chấm phẩy / xuống dòng cho dữ liệu nhập kiểu cũ.
    Dấu - chỉ tách khi MỌI mảnh đều đủ dài như một số điện thoại (>= 8 chữ số) — số viết 0938-016-788 giữ nguyên.
    Bỏ mục rỗng và số trùng, giữ thứ tự nhập."""
    ra = []
    for manh in re.split(r'[,;\n]+', str(value or '')):
        manh = manh.strip()
        con = [c for c in re.split(r'\s*[-\u2013\u2014]\s*', manh) if c]
        if len(con) > 1 and all(len(re.sub(r'\D', '', c)) >= 8 for c in con):
            ds = con
        else:
            ds = [manh]
        for so in ds:
            so = so.strip()
            if so and so not in ra:
                ra.append(so)
    return ra
