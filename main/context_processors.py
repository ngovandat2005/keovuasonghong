from .models import ThemeSettings, DealerRegistration, ConsultationRequest, ContactMessage, Catalogue

def theme_settings(request):
    """
    Nạp cấu hình giao diện và thông báo vào toàn cục template.
    """
    settings_obj = ThemeSettings.load()
    notifications_count = 0
    try:
        pending_dealers = DealerRegistration.objects.filter(is_processed=False).count()
        pending_consult = ConsultationRequest.objects.filter(is_processed=False).count()
        unread_contacts = ContactMessage.objects.filter(is_read=False).count()
        notifications_count = pending_dealers + pending_consult + unread_contacts
    except Exception:
        pass

    # Link file của Hồ sơ năng lực / Hồ sơ kỹ thuật (lấy từ E-Catalog) cho chân trang
    footer_doc_urls = {}
    try:
        for cat in Catalogue.objects.filter(is_active=True, slug__in=['ho-so-nang-luc', 'ho-so-ky-thuat']):
            if cat.file_url:
                footer_doc_urls[cat.slug.replace('-', '_')] = cat.file_url
    except Exception:
        pass

    return {
        'footer_doc_urls': footer_doc_urls,
        'theme': settings_obj,
        'notifications_count': notifications_count if notifications_count > 0 else 9,
        'real_notifications_count': notifications_count,
    }
