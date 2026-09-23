from .models import ThemeSettings, DealerRegistration, ConsultationRequest, ContactMessage

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

    return {
        'theme': settings_obj,
        'notifications_count': notifications_count if notifications_count > 0 else 9,
        'real_notifications_count': notifications_count,
    }
