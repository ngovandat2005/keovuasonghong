"""Số đơn chưa xử lý hiển thị cạnh mục menu bên trái trang admin (Unfold sidebar badge)."""
from .models import DealerRegistration, ConsultationRequest


def dealer_registration_badge(request):
    count = DealerRegistration.objects.filter(is_processed=False).count()
    return count or None


def consultation_request_badge(request):
    count = ConsultationRequest.objects.filter(is_processed=False).count()
    return count or None
