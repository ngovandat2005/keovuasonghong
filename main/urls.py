from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('gioi-thieu/', views.about, name='about'),
    path('san-pham/', views.product_list, name='product_list'),
    path('san-pham/<slug:category>/', views.product_list, name='product_list_category'),
    path('san-pham/<slug:category>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('tin-tuc/', views.news_list, name='news_list'),
    path('tin-tuc/<slug:category>/', views.news_list, name='news_list_category'),
    path('tin-tuc/<slug:category>/<slug:slug>/', views.news_detail, name='news_detail'),
    path('chinh-sach-va-dieu-khoan/', views.policy, name='policy'),
    path('dai-ly-phan-phoi/', views.distributors, name='distributors'),
    path('dang-ky-dai-ly/', views.dealer_register, name='dealer_register'),
    path('lien-he/', views.contact, name='contact'),
    path('e-catalog/', views.catalogue, name='catalogue'),
    path('catalogue/', views.catalogue, name='catalogue_alias'),
    path('cong-cu-tinh/', views.calculator, name='calculator'),
    path('du-an/', views.project_list, name='project_list'),
    path('du-an/danh-muc/<slug:category>/', views.project_category_redirect, name='project_category_legacy_redirect'),
    path('du-an/<slug:category>/', views.project_list, name='project_list_category'),
    path('du-an/<slug:category>/<slug:slug>/', views.project_detail, name='project_detail'),
    path('dang-ky-tu-van/', views.consultation, name='consultation'),
    path('xuat-excel-tu-van/', views.download_consultations_excel, name='export_consultations_excel'),
    path('xuat-word-tu-van/<int:pk>/', views.download_consultation_word, name='export_consultation_word'),
]

