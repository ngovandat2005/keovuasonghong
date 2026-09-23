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
