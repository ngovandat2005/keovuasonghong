from django import template
from main.models import Product, Project, ConsultationRequest, DealerRegistration, ContactMessage

register = template.Library()

@register.simple_tag
def get_dashboard_stats():
    return {
        'total_products': Product.objects.count(),
        'total_projects': Project.objects.count(),
        'new_consultations': ConsultationRequest.objects.filter(is_processed=False).count(),
        'new_dealers': DealerRegistration.objects.filter(is_processed=False).count(),
        'unread_contacts': ContactMessage.objects.filter(is_read=False).count(),
    }
