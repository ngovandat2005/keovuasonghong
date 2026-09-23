from django import forms
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import (ProductCategory, Product, ProductImage,
                     NewsCategory, News,
                     Banner, Distributor, DistributorLink, DealerRegistration, ContactMessage,
                     Project, ProjectCategory, ConsultationRequest, Catalogue, CATALOGUE_GROUP_CHOICES, ThemeSettings,
                     HomeBanner, Partner, AboutGalleryImage)


class ThumbnailClearableFileInput(forms.ClearableFileInput):
    template_name = 'admin/main/product/widgets/thumbnail_file_input.html'


def clean_changelist_request_get(model_admin, request, allowed_per_page=(10, 20, 50, 100)):
    if request.GET:
        cleaned_get = request.GET.copy()
        for key in list(cleaned_get.keys()):
            if cleaned_get[key] == '':
                del cleaned_get[key]
        if 'list_per_page' in cleaned_get:
            try:
                per_page = int(cleaned_get['list_per_page'])
                if per_page in allowed_per_page:
                    model_admin.list_per_page = per_page
            except (TypeError, ValueError):
                pass
            del cleaned_get['list_per_page']
        request.GET = cleaned_get


def get_shared_media_library_response(request):
    import os
    from django.http import JsonResponse
    from django.conf import settings

    img_type = request.GET.get('type', 'uploaded')  # 'products' or 'uploaded'
    try:
        page = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    page_size = 15

    items = []

    if img_type == 'products':
        # 1. Product avatar
        for p in Product.objects.exclude(image='').exclude(image__isnull=True).order_by('-id'):
            try:
                if p.image and p.image.url:
                    items.append({'url': p.image.url, 'name': p.name})
            except Exception:
                pass
        # 2. Product gallery images
        for pi in ProductImage.objects.exclude(image='').exclude(image__isnull=True).order_by('-id'):
            try:
                if pi.image and pi.image.url:
                    items.append({'url': pi.image.url, 'name': getattr(pi.product, 'name', '')})
            except Exception:
                pass
    else:  # 'uploaded'
        # 1. Scan folders
        for sub in ['news/content', 'products/content', 'products/gallery', 'products']:
            content_dir = os.path.join(settings.MEDIA_ROOT, *sub.split('/'))
            if os.path.exists(content_dir):
                files = sorted(
                    [f for f in os.listdir(content_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'))],
                    key=lambda x: os.path.getmtime(os.path.join(content_dir, x)),
                    reverse=True
                )
                for f in files:
                    url = f"{settings.MEDIA_URL}{sub}/{f}"
                    items.append({'url': url, 'name': f})

        # 2. News avatar images
        for n in News.objects.exclude(image='').exclude(image__isnull=True).order_by('-id'):
            try:
                if n.image and n.image.url:
                    items.append({'url': n.image.url, 'name': n.title})
            except Exception:
                pass

        # 3. Project images
        for pr in Project.objects.exclude(image='').exclude(image__isnull=True).order_by('-id'):
            try:
                if pr.image and pr.image.url:
                    items.append({'url': pr.image.url, 'name': pr.title})
            except Exception:
                pass

    # Deduplicate items by url while preserving order
    unique_items = []
    seen_urls = set()
    for item in items:
        if item['url'] not in seen_urls:
            seen_urls.add(item['url'])
            unique_items.append(item)

    total_count = len(unique_items)
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    page = min(max(1, page), total_pages)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = unique_items[start_idx:end_idx]

    return JsonResponse({
        'items': page_items,
        'total_count': total_count,
        'total_pages': total_pages,
        'current_page': page,
    })


def handle_shared_content_image_upload(request, folder='news/content'):
    from django.http import JsonResponse
    file = request.FILES.get('file')
    if not file or not (file.content_type or '').startswith('image/'):
        return JsonResponse({'error': 'Vui lòng chọn một file ảnh hợp lệ.'}, status=400)
    from django.core.files.storage import default_storage
    saved_path = default_storage.save(f'{folder}/{file.name}', file)
    return JsonResponse({'location': default_storage.url(saved_path)})


@admin.register(ProductCategory)
class ProductCategoryAdmin(ModelAdmin):
    change_list_template = 'admin/main/productcategory/change_list.html'
    change_form_template = 'admin/main/productcategory/change_form.html'
    list_fullwidth = True
    list_display = ['name', 'slug', 'products_count']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

    def products_count(self, obj):
        return obj.product_set.count()
    products_count.short_description = "Số lượng sản phẩm"

    def changelist_view(self, request, extra_context=None):
        clean_changelist_request_get(self, request)
        extra_context = extra_context or {}
        extra_context['total_count'] = ProductCategory.objects.count()
        response = super().changelist_view(request, extra_context)
        cl = getattr(response, 'context_data', {}).get('cl')
        if cl is not None:
            page = cl.paginator.page(cl.page_num)
            response.context_data['range_start'] = page.start_index()
            response.context_data['range_end'] = page.end_index()
        return response


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 0
    fields = ['media_type', 'image', 'image_url', 'video_url', 'order']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'image':
            formfield.widget = forms.FileInput()
        elif db_field.name == 'media_type':
            formfield.widget.attrs['class'] = 'pd-media-type-select'
        return formfield


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    change_list_template = 'admin/main/product/change_list.html'
    change_form_template = 'admin/main/product/change_form.html'
    list_fullwidth = True
    list_display = ['name', 'sku', 'category', 'is_featured', 'is_active', 'created_at']
    list_filter = ['category', 'is_featured', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'sku', 'slug', 'category__name', 'short_description', 'description', 'usage_norms', 'specifications']
    ordering = ['order', 'id']
    inlines = [ProductImageInline]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'image':
            formfield.widget = ThumbnailClearableFileInput()
        elif db_field.name == 'video_url':
            formfield.widget = forms.URLInput(attrs={
                'placeholder': 'https://www.youtube.com/watch?v=... (Dán link video YouTube, để trống nếu không dùng)',
                'style': 'width: 100%; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13.5px;'
            })
        return formfield

    fieldsets = (
        (None, {'fields': ('name', 'sku', 'slug', 'category', 'order')}),
        ('Media', {'fields': ('image', 'video_url'), 'classes': ('tab-media',)}),
        ('Tài liệu', {'fields': ('ecatalog_file', 'certificate_file'), 'classes': ('tab-media',)}),
        ('Thông tin chung', {'fields': ('short_description',), 'classes': ('tab-general',)}),
        ('Hướng dẫn thi công', {'fields': ('description',), 'classes': ('tab-guide',)}),
        ('Định mức sử dụng', {'fields': ('usage_norms',), 'classes': ('tab-norms',)}),
        ('Thông tin sản phẩm', {'fields': ('specifications',)}),
    )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('toggle-active/<int:pk>/', self.admin_site.admin_view(self.toggle_active), name='main_product_toggle_active'),
            path('update-order/<int:pk>/', self.admin_site.admin_view(self.update_order), name='main_product_update_order'),
            path('reorder-products/', self.admin_site.admin_view(self.reorder_products), name='main_product_reorder_products'),
            path('reorder-gallery/<int:pk>/', self.admin_site.admin_view(self.reorder_gallery), name='main_product_reorder_gallery'),
            path('upload-content-image/', self.admin_site.admin_view(self.upload_content_image), name='main_product_upload_content_image'),
            path('list-media-images/', self.admin_site.admin_view(self.list_media_images), name='main_product_list_media_images'),
        ]
        return custom_urls + urls

    def list_media_images(self, request):
        if not (request.user.is_staff or request.user.has_perm('main.change_product') or request.user.has_perm('main.add_product')):
            from django.http import JsonResponse
            return JsonResponse({'error': 'forbidden'}, status=403)
        return get_shared_media_library_response(request)

    def upload_content_image(self, request):
        if not (request.user.is_staff or request.user.has_perm('main.change_product') or request.user.has_perm('main.add_product')):
            from django.http import JsonResponse
            return JsonResponse({'error': 'forbidden'}, status=403)
        return handle_shared_content_image_upload(request, folder='products/content')

    def reorder_products(self, request):
        import json
        from django.http import JsonResponse
        if request.method != 'POST' or not request.user.has_perm('main.change_product'):
            return JsonResponse({'ok': False}, status=403)
        try:
            data = json.loads(request.body)
            pks = data.get('pks', [])
            start_order = int(data.get('start_order', 0))
            for i, pk in enumerate(pks):
                Product.objects.filter(pk=pk).update(order=start_order + i)
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    def reorder_gallery(self, request, pk):
        import json
        from django.http import JsonResponse
        if request.method != 'POST' or not request.user.has_perm('main.change_product'):
            return JsonResponse({'ok': False}, status=403)
        try:
            data = json.loads(request.body)
            product = Product.objects.get(pk=pk)
            avatar_id = data.get('avatar_id')
            gallery_order = data.get('gallery_order', [])

            if avatar_id and str(avatar_id).startswith('gallery_image_'):
                g_id = int(str(avatar_id).replace('gallery_image_', ''))
                try:
                    g_img = ProductImage.objects.get(id=g_id, product=product)
                    old_avatar_file = product.image.name if product.image else None
                    if g_img.image:
                        product.image.name = g_img.image.name
                        product.save(update_fields=['image'])
                        if old_avatar_file:
                            g_img.image.name = old_avatar_file
                            g_img.save(update_fields=['image'])
                        else:
                            g_img.delete()
                except ProductImage.DoesNotExist:
                    pass

            for idx, g_pk in enumerate(gallery_order):
                ProductImage.objects.filter(pk=g_pk, product=product).update(order=idx)

            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        product = form.instance
        avatar_id = request.POST.get('selected_avatar_id')
        if avatar_id and str(avatar_id).startswith('gallery_image_'):
            try:
                g_id = int(str(avatar_id).replace('gallery_image_', ''))
                g_img = ProductImage.objects.get(id=g_id, product=product)
                old_avatar_file = product.image.name if product.image else None
                if g_img.image:
                    product.image.name = g_img.image.name
                    product.save(update_fields=['image'])
                    if old_avatar_file:
                        g_img.image.name = old_avatar_file
                        g_img.save(update_fields=['image'])
                    else:
                        g_img.delete()
            except Exception:
                pass



    def toggle_active(self, request, pk):
        from django.http import JsonResponse
        if request.method != 'POST' or not request.user.has_perm('main.change_product'):
            return JsonResponse({'ok': False}, status=403)
        product = Product.objects.get(pk=pk)
        product.is_active = not product.is_active
        product.save(update_fields=['is_active'])
        return JsonResponse({'ok': True, 'is_active': product.is_active})

    def update_order(self, request, pk):
        from django.http import JsonResponse
        if request.method != 'POST' or not request.user.has_perm('main.change_product'):
            return JsonResponse({'ok': False}, status=403)
        try:
            value = int(request.POST.get('order', 0))
        except (TypeError, ValueError):
            return JsonResponse({'ok': False}, status=400)
        product = Product.objects.get(pk=pk)
        product.order = value
        product.save(update_fields=['order'])
        return JsonResponse({'ok': True, 'order': product.order})

    def changelist_view(self, request, extra_context=None):
        clean_changelist_request_get(self, request, allowed_per_page=(10, 20, 50, 100))
        extra_context = extra_context or {}
        current_category = request.GET.get('category__id__exact', '')
        categories = []
        for cat in ProductCategory.objects.all():
            categories.append({'obj': cat, 'count': Product.objects.filter(category=cat).count()})
        extra_context['product_categories'] = categories
        extra_context['total_count'] = Product.objects.count()
        extra_context['current_category'] = current_category
        extra_context['current_is_active'] = request.GET.get('is_active__exact', '')
        response = super().changelist_view(request, extra_context)
        cl = getattr(response, 'context_data', {}).get('cl')
        if cl is not None:
            try:
                page = cl.paginator.page(cl.page_num)
                response.context_data['range_start'] = page.start_index()
                response.context_data['range_end'] = page.end_index()
            except Exception:
                pass
        return response


@admin.register(NewsCategory)
class NewsCategoryAdmin(ModelAdmin):
    change_list_template = 'admin/main/newscategory/change_list.html'
    list_fullwidth = True
    list_display = ['name', 'slug', 'news_count']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

    def news_count(self, obj):
        return obj.news_set.count()
    news_count.short_description = "Số lượng bài viết"

    def changelist_view(self, request, extra_context=None):
        clean_changelist_request_get(self, request)
        extra_context = extra_context or {}
        extra_context['total_count'] = NewsCategory.objects.count()
        response = super().changelist_view(request, extra_context)
        cl = getattr(response, 'context_data', {}).get('cl')
        if cl is not None:
            page = cl.paginator.page(cl.page_num)
            response.context_data['range_start'] = page.start_index()
            response.context_data['range_end'] = page.end_index()
        return response


@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    list_display = ['title', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title']


@admin.register(DealerRegistration)
class DealerRegistrationAdmin(ModelAdmin):
    change_list_template = 'admin/main/dealerregistration/change_list.html'
    change_form_template = 'admin/main/dealerregistration/change_form.html'
    list_fullwidth = True
    list_display = ['company', 'full_name', 'phone', 'province', 'tax_id', 'created_at', 'is_processed']
    list_filter = ['is_processed', 'province']
    search_fields = ['company', 'full_name', 'phone', 'tax_id', 'email', 'province', 'address']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    actions = ['export_to_excel_action', 'export_to_word_action']
    fieldsets = (
        ('Thông tin doanh nghiệp', {
            'fields': ('company', 'full_name', 'phone', 'email', 'tax_id')
        }),
        ('Khu vực & Địa chỉ', {
            'fields': ('province', 'address')
        }),
        ('Nội dung đăng ký', {
            'fields': ('products_distributed', 'note')
        }),
        ('Trạng thái tiếp nhận', {
            'fields': ('is_processed', 'created_at')
        }),
    )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('toggle-processed/<int:pk>/', self.admin_site.admin_view(self.toggle_processed), name='main_dealerregistration_toggle_processed'),
            path('export-word/<int:pk>/', self.admin_site.admin_view(self.export_single_word), name='main_dealerregistration_export_word'),
            path('export-all-excel/', self.admin_site.admin_view(self.export_all_excel), name='main_dealerregistration_export_all_excel'),
        ]
        return custom_urls + urls

    def toggle_processed(self, request, pk):
        from django.http import JsonResponse
        if request.method != 'POST' or not request.user.has_perm('main.change_dealerregistration'):
            return JsonResponse({'ok': False, 'error': 'Forbidden'}, status=403)
        try:
            item = DealerRegistration.objects.get(pk=pk)
            item.is_processed = not item.is_processed
            item.save(update_fields=['is_processed'])
            return JsonResponse({'ok': True, 'is_processed': item.is_processed})
        except DealerRegistration.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)

    def export_single_word(self, request, pk):
        from io import BytesIO
        from django.http import HttpResponse
        from .export_utils import export_dealer_to_docx
        try:
            item = DealerRegistration.objects.get(pk=pk)
            doc = export_dealer_to_docx(item)
            doc_io = BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)
            response = HttpResponse(
                doc_io.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            safe_phone = str(item.phone).replace(' ', '')
            response['Content-Disposition'] = f'attachment; filename="Phieu_Dai_Ly_{item.pk}_{safe_phone}.docx"'
            return response
        except DealerRegistration.DoesNotExist:
            from django.http import Http404
            raise Http404("Không tìm thấy")

    def export_all_excel(self, request):
        from django.http import HttpResponse
        from django.utils import timezone
        from .export_utils import export_dealers_to_excel
        qs = DealerRegistration.objects.all().order_by('-created_at')
        wb = export_dealers_to_excel(qs)
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Danh_Sach_Dang_Ky_Dai_Ly_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
        wb.save(response)
        return response

    @admin.action(description="📥 Xuất danh sách đã chọn ra file Excel (.xlsx)")
    def export_to_excel_action(self, request, queryset):
        from django.http import HttpResponse
        from django.utils import timezone
        from .export_utils import export_dealers_to_excel
        wb = export_dealers_to_excel(queryset)
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Danh_Sach_Dai_Ly_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
        wb.save(response)
        return response

    @admin.action(description="📄 Xuất phiếu tiếp nhận đã chọn ra file Word (.docx)")
    def export_to_word_action(self, request, queryset):
        from io import BytesIO
        from django.http import HttpResponse
        from django.utils import timezone
        from .export_utils import export_dealer_to_docx
        from docx import Document
        combined_doc = Document()
        first = True
        for obj in queryset:
            if not first:
                combined_doc.add_page_break()
            export_dealer_to_docx(obj, doc=combined_doc)
            first = False
        doc_io = BytesIO()
        combined_doc.save(doc_io)
        doc_io.seek(0)
        response = HttpResponse(
            doc_io.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="Phieu_Dang_Ky_Dai_Ly_{timezone.now().strftime("%Y%m%d_%H%M")}.docx"'
        return response

    def changelist_view(self, request, extra_context=None):
        clean_changelist_request_get(self, request)
        extra_context = extra_context or {}
        extra_context['total_count'] = DealerRegistration.objects.count()
        extra_context['pending_count'] = DealerRegistration.objects.filter(is_processed=False).count()
        extra_context['done_count'] = DealerRegistration.objects.filter(is_processed=True).count()
        extra_context['current_status'] = request.GET.get('is_processed__exact', '')
        extra_context['current_province'] = request.GET.get('province__exact', '')
        from django.db.models import Count
        extra_context['province_list'] = DealerRegistration.objects.exclude(province='').values('province').annotate(count=Count('id')).order_by('-count')[:15]
        return super().changelist_view(request, extra_context)



@admin.register(ContactMessage)
class ContactMessageAdmin(ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'created_at', 'is_read']
    list_editable = ['is_read']
    readonly_fields = ['created_at']
    search_fields = ['full_name', 'phone']


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(ModelAdmin):
    change_list_template = 'admin/main/projectcategory/change_list.html'
    list_fullwidth = True
    list_display = ['name', 'slug']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

    def changelist_view(self, request, extra_context=None):
        clean_changelist_request_get(self, request)
        extra_context = extra_context or {}
        extra_context['total_count'] = ProjectCategory.objects.count()
        response = super().changelist_view(request, extra_context)
        cl = getattr(response, 'context_data', {}).get('cl')
        if cl is not None:
            page = cl.paginator.page(cl.page_num)
            response.context_data['range_start'] = page.start_index()
            response.context_data['range_end'] = page.end_index()
            for obj in cl.result_list:
                obj.count = Project.objects.filter(category=obj.slug).count()
        return response


class ProjectAdminForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'slug', 'category', 'author', 'image', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Nhập tên dự án...'}),
            'slug': forms.TextInput(attrs={'placeholder': 'duong-dan-du-an-tu-dong'}),
            'author': forms.TextInput(attrs={'placeholder': 'VD: Công ty TNHH Keo Vữa Sông Hồng'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'slug' in self.fields:
            self.fields['slug'].required = False
            self.fields['slug'].label = 'Đường dẫn tĩnh (Slug)'


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    change_list_template = 'admin/main/project/change_list.html'
    change_form_template = 'admin/main/project/change_form.html'
    form = ProjectAdminForm
    list_fullwidth = True
    list_display = ['title_with_image', 'category', 'author', 'is_active', 'published_at', 'updated_at']
    list_filter = ['category', 'author', 'is_active']
    search_fields = ['title', 'client', 'location', 'author', 'category']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    ordering = ['-published_at']
    fields = ['title', 'slug', 'category', 'author', 'image', 'description']

    def save_model(self, request, obj, form, change):
        if not obj.slug or not str(obj.slug).strip():
            from .models import vietnamese_slugify
            obj.slug = vietnamese_slugify(obj.title)
        super().save_model(request, obj, form, change)

    actions = ['bulk_edit_action']

    @admin.action(description='Chỉnh sửa các dự án đã chọn')
    def bulk_edit_action(self, request, queryset):
        from django.shortcuts import redirect
        from django.urls import reverse
        pks = ','.join(str(p.pk) for p in queryset)
        return redirect(f"{reverse('admin:main_project_bulk_edit')}?ids={pks}")

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('bulk-edit/', self.admin_site.admin_view(self.bulk_edit_view), name='main_project_bulk_edit'),
            path('toggle-active/<int:pk>/', self.admin_site.admin_view(self.toggle_active), name='main_project_toggle_active'),
            path('upload-content-image/', self.admin_site.admin_view(self.upload_content_image), name='main_project_upload_content_image'),
            path('list-media-images/', self.admin_site.admin_view(self.list_media_images), name='main_project_list_media_images'),
        ]
        return custom_urls + urls

    def list_media_images(self, request):
        if not (request.user.is_staff or request.user.has_perm('main.change_project') or request.user.has_perm('main.add_project')):
            from django.http import JsonResponse
            return JsonResponse({'error': 'forbidden'}, status=403)
        return get_shared_media_library_response(request)

    def upload_content_image(self, request):
        if not (request.user.is_staff or request.user.has_perm('main.change_project') or request.user.has_perm('main.add_project')):
            from django.http import JsonResponse
            return JsonResponse({'error': 'forbidden'}, status=403)
        return handle_shared_content_image_upload(request, folder='projects/content')

    def bulk_edit_view(self, request):
        from django.shortcuts import render, redirect
        from django.contrib import messages
        from .models import PROJECT_CATEGORY_CHOICES

        if not request.user.has_perm('main.change_project'):
            messages.error(request, 'Bạn không có quyền chỉnh sửa dự án.')
            return redirect('admin:main_project_changelist')

        if request.method == 'POST':
            pks = request.POST.getlist('project_ids')
            updated_count = 0
            for pk in pks:
                try:
                    project = Project.objects.get(pk=pk)
                    title = request.POST.get(f'title_{pk}')
                    category = request.POST.get(f'category_{pk}')
                    author = request.POST.get(f'author_{pk}')
                    client = request.POST.get(f'client_{pk}')
                    location = request.POST.get(f'location_{pk}')
                    is_active = request.POST.get(f'is_active_{pk}') == '1'

                    if title:
                        project.title = title.strip()
                    if category:
                        project.category = category.strip()
                    if author is not None:
                        project.author = author.strip()
                    if client is not None:
                        project.client = client.strip()
                    if location is not None:
                        project.location = location.strip()
                    project.is_active = is_active
                    project.save()
                    updated_count += 1
                except Project.DoesNotExist:
                    continue

            messages.success(request, f'Đã cập nhật thành công {updated_count} dự án.')
            return redirect('admin:main_project_changelist')

        ids_str = request.GET.get('ids', '')
        if ids_str:
            id_list = [int(x.strip()) for x in ids_str.split(',') if x.strip().isdigit()]
            projects = Project.objects.filter(id__in=id_list).order_by('order', 'id')
        else:
            projects = Project.objects.all().order_by('order', 'id')

        context = {
            **self.admin_site.each_context(request),
            'title': 'Chỉnh sửa nhiều dự án',
            'projects': projects,
            'categories': PROJECT_CATEGORY_CHOICES,
            'opts': self.model._meta,
        }
        return render(request, 'admin/main/project/bulk_edit.html', context)

    def toggle_active(self, request, pk):
        from django.http import JsonResponse
        if request.method != 'POST' or not request.user.has_perm('main.change_project'):
            return JsonResponse({'ok': False}, status=403)
        project = Project.objects.get(pk=pk)
        project.is_active = not project.is_active
        project.save(update_fields=['is_active'])
        return JsonResponse({'ok': True, 'is_active': project.is_active})


    def changelist_view(self, request, extra_context=None):
        clean_changelist_request_get(self, request)
        extra_context = extra_context or {}
        current_category = request.GET.get('category__exact', '')
        
        # Build category list for tabs
        from .models import PROJECT_CATEGORY_CHOICES
        cat_map = dict(PROJECT_CATEGORY_CHOICES)
        try:
            for cat_obj in ProjectCategory.objects.all():
                cat_map[cat_obj.slug] = cat_obj.name
        except Exception:
            pass
            
        categories = []
        for slug, name in cat_map.items():
            count = Project.objects.filter(category=slug).count()
            categories.append({'slug': slug, 'name': name, 'count': count})
            
        extra_context['project_categories'] = categories
        extra_context['total_count'] = Project.objects.count()
        extra_context['current_category'] = current_category
        extra_context['current_is_active'] = request.GET.get('is_active__exact', '')
        response = super().changelist_view(request, extra_context)
        cl = getattr(response, 'context_data', {}).get('cl')
        if cl is not None:
            try:
                page = cl.paginator.page(cl.page_num)
                response.context_data['range_start'] = page.start_index()
                response.context_data['range_end'] = page.end_index()
            except Exception:
                pass
        return response

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            try:
                cats = list(ProjectCategory.objects.all())
                if cats:
                    kwargs['widget'] = forms.Select(choices=[(c.slug, c.name) for c in cats])
            except Exception:
                pass
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    @admin.display(description='Tiêu đề')
    def title_with_image(self, obj):
        from django.utils.html import format_html
        style = "color: #007bff; font-size: 11px;"
        if obj.image:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 10px;">'
                '<img src="{}" style="width: 40px; height: 30px; object-fit: cover; border-radius: 4px;" />'
                '<span style="{}">{}</span>'
                '</div>',
                obj.image.url, style, obj.title
            )
        return format_html('<span style="{}">{}</span>', style, obj.title)


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(ModelAdmin):
    change_list_template = 'admin/main/consultationrequest/change_list.html'
    change_form_template = 'admin/main/consultationrequest/change_form.html'
    list_fullwidth = True
    list_display = ['full_name', 'phone', 'company', 'interest', 'created_at', 'is_processed']
    list_filter = ['is_processed']
    search_fields = ['full_name', 'phone', 'company', 'email', 'interest', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    actions = ['export_to_excel_action', 'export_to_word_action']
    fieldsets = (
        ('Thông tin khách hàng', {
            'fields': ('full_name', 'phone', 'email', 'company')
        }),
        ('Nội dung yêu cầu tư vấn', {
            'fields': ('interest', 'message')
        }),
        ('Trạng thái xử lý', {
            'fields': ('is_processed', 'created_at')
        }),
    )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('toggle-processed/<int:pk>/', self.admin_site.admin_view(self.toggle_processed), name='main_consultationrequest_toggle_processed'),
            path('export-word/<int:pk>/', self.admin_site.admin_view(self.export_single_word), name='main_consultationrequest_export_word'),
            path('export-all-excel/', self.admin_site.admin_view(self.export_all_excel), name='main_consultationrequest_export_all_excel'),
        ]
        return custom_urls + urls

    def toggle_processed(self, request, pk):
        from django.http import JsonResponse
        if request.method != 'POST' or not request.user.has_perm('main.change_consultationrequest'):
            return JsonResponse({'ok': False, 'error': 'Forbidden'}, status=403)
        try:
            item = ConsultationRequest.objects.get(pk=pk)
            item.is_processed = not item.is_processed
            item.save(update_fields=['is_processed'])
            return JsonResponse({'ok': True, 'is_processed': item.is_processed})
        except ConsultationRequest.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)

    def export_single_word(self, request, pk):
        from io import BytesIO
        from django.http import HttpResponse
        from .export_utils import export_consultation_to_docx
        try:
            item = ConsultationRequest.objects.get(pk=pk)
            doc = export_consultation_to_docx(item)
            doc_io = BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)
            response = HttpResponse(
                doc_io.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            safe_phone = str(item.phone).replace(' ', '')
            response['Content-Disposition'] = f'attachment; filename="Phieu_Tu_Van_{item.pk}_{safe_phone}.docx"'
            return response
        except ConsultationRequest.DoesNotExist:
            from django.http import Http404
            raise Http404("Không tìm thấy")

    def export_all_excel(self, request):
        from django.http import HttpResponse
        from django.utils import timezone
        from .export_utils import export_consultations_to_excel
        qs = ConsultationRequest.objects.all().order_by('-created_at')
        wb = export_consultations_to_excel(qs)
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Danh_Sach_Tu_Van_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
        wb.save(response)
        return response

    @admin.action(description="📥 Xuất danh sách đã chọn ra file Excel (.xlsx)")
    def export_to_excel_action(self, request, queryset):
        from django.http import HttpResponse
        from django.utils import timezone
        from .export_utils import export_consultations_to_excel

        wb = export_consultations_to_excel(queryset)
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Danh_Sach_Tu_Van_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
        wb.save(response)
        return response

    @admin.action(description="📄 Xuất phiếu tư vấn đã chọn ra file Word (.docx)")
    def export_to_word_action(self, request, queryset):
        from io import BytesIO
        from django.http import HttpResponse
        from django.utils import timezone
        from .export_utils import export_consultation_to_docx
        from docx import Document

        # Tạo file word gộp tất cả phiếu được chọn
        combined_doc = Document()
        first = True
        for obj in queryset:
            if not first:
                combined_doc.add_page_break()
            export_consultation_to_docx(obj, doc=combined_doc)
            first = False

        doc_io = BytesIO()
        combined_doc.save(doc_io)
        doc_io.seek(0)

        response = HttpResponse(
            doc_io.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="Phieu_Dang_Ky_Tu_Van_{timezone.now().strftime("%Y%m%d_%H%M")}.docx"'
        return response

    def changelist_view(self, request, extra_context=None):
        clean_changelist_request_get(self, request)
        extra_context = extra_context or {}
        extra_context['total_count'] = ConsultationRequest.objects.count()
        extra_context['pending_count'] = ConsultationRequest.objects.filter(is_processed=False).count()
        extra_context['done_count'] = ConsultationRequest.objects.filter(is_processed=True).count()
        extra_context['current_status'] = request.GET.get('is_processed__exact', '')
        return super().changelist_view(request, extra_context)


class CatalogueAdminForm(forms.ModelForm):
    class Meta:
        model = Catalogue
        fields = ['title', 'slug', 'group_name', 'description', 'thumbnail', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'VD: Catalogue sản phẩm Keo dán gạch C2'}),
            'group_name': forms.Select(choices=CATALOGUE_GROUP_CHOICES),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Mô tả ngắn gọn về tài liệu này (không bắt buộc)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'slug' in self.fields:
            self.fields['slug'].required = False
        if 'file' in self.fields:
            self.fields['file'].required = False
        if 'thumbnail' in self.fields:
            self.fields['thumbnail'].required = False


@admin.register(Catalogue)
class CatalogueAdmin(ModelAdmin):
    change_list_template = 'admin/main/catalogue/change_list.html'
    change_form_template = 'admin/main/catalogue/change_form.html'
    form = CatalogueAdminForm
    list_fullwidth = True
    list_display = ['title', 'group_name', 'order', 'is_active', 'created_at']
    list_filter = ['group_name', 'is_active']
    search_fields = ['title', 'group_name', 'description']
    ordering = ['group_name', 'order', 'title']

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('toggle-active/<int:pk>/', self.admin_site.admin_view(self.toggle_active), name='main_catalogue_toggle_active'),
        ]
        return custom_urls + urls

    def toggle_active(self, request, pk):
        from django.http import JsonResponse
        if request.method != 'POST' or not request.user.has_perm('main.change_catalogue'):
            return JsonResponse({'ok': False}, status=403)
        try:
            cat = Catalogue.objects.get(pk=pk)
            cat.is_active = not cat.is_active
            cat.save(update_fields=['is_active'])
            return JsonResponse({'ok': True, 'is_active': cat.is_active})
        except Catalogue.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)

    def changelist_view(self, request, extra_context=None):
        clean_changelist_request_get(self, request)
        extra_context = extra_context or {}
        current_group = request.GET.get('group_name__exact', '')

        tabs = []
        for val, label in CATALOGUE_GROUP_CHOICES:
            count = Catalogue.objects.filter(group_name=val).count()
            tabs.append({'slug': val, 'name': label, 'count': count})

        extra_context['group_tabs'] = tabs
        extra_context['total_count'] = Catalogue.objects.count()
        extra_context['current_group'] = current_group
        extra_context['current_is_active'] = request.GET.get('is_active__exact', '')
        response = super().changelist_view(request, extra_context)
        cl = getattr(response, 'context_data', {}).get('cl')
        if cl is not None:
            try:
                page = cl.paginator.page(cl.page_num)
                response.context_data['range_start'] = page.start_index()
                response.context_data['range_end'] = page.end_index()
            except Exception:
                pass
        return response


class NewsAdminForm(forms.ModelForm):
    published_at = forms.DateTimeField(
        required=False,
        label='Ngày đăng',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
    )

    class Meta:
        model = News
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Nhập tiêu đề tin tức...'}),
            'slug': forms.TextInput(attrs={'placeholder': 'duong-dan-tin-tuc-tu-dong'}),
            'author': forms.TextInput(attrs={'placeholder': 'VD: Công ty TNHH Keo Vữa Sông Hồng'}),
            'image_url': forms.URLInput(attrs={'placeholder': 'https://... (dùng khi không có sẵn file ảnh)'}),
            'video_url': forms.URLInput(attrs={'placeholder': 'https://www.youtube.com/watch?v=... hoặc https://youtu.be/...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'slug' in self.fields:
            self.fields['slug'].required = False
            self.fields['slug'].label = 'Đường dẫn tĩnh (Slug)'
        if 'order' in self.fields:
            self.fields['order'].required = False


@admin.register(News)
class NewsAdmin(ModelAdmin):
    change_list_template = 'admin/main/news/change_list.html'
    change_form_template = 'admin/main/news/change_form.html'
    form = NewsAdminForm
    list_fullwidth = True
    list_display = ['title_with_image', 'category', 'author', 'is_active', 'published_at', 'updated_at']
    list_filter = ['category', 'author', 'is_active']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'author', 'category__name', 'summary']
    date_hierarchy = 'published_at'
    ordering = ['-published_at']
    fields = ['title', 'slug', 'category', 'author', 'image', 'image_url', 'video_url', 'summary', 'content', 'published_at', 'is_active']

    def save_model(self, request, obj, form, change):
        if not obj.published_at:
            from django.utils import timezone
            obj.published_at = timezone.now()
        if not obj.slug or not str(obj.slug).strip():
            from .models import vietnamese_slugify
            obj.slug = vietnamese_slugify(obj.title)
        # Nếu admin lỡ dán link YouTube vào ô "Link ảnh", tự động chuyển sang video_url
        if obj.image_url and not obj.video_url:
            u = obj.image_url.strip()
            if 'youtube.com/watch' in u or 'youtube.com/shorts' in u or 'youtube.com/embed' in u or 'youtu.be/' in u:
                obj.video_url = u
                obj.image_url = ''
        super().save_model(request, obj, form, change)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            kwargs['widget'] = forms.Select()
        elif db_field.name == 'is_active':
            kwargs['widget'] = forms.CheckboxInput()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('toggle-active/<int:pk>/', self.admin_site.admin_view(self.toggle_active), name='main_news_toggle_active'),
            path('upload-content-image/', self.admin_site.admin_view(self.upload_content_image), name='main_news_upload_content_image'),
            path('list-media-images/', self.admin_site.admin_view(self.list_media_images), name='main_news_list_media_images'),
        ]
        return custom_urls + urls

    def list_media_images(self, request):
        if not (request.user.is_staff or request.user.has_perm('main.change_news') or request.user.has_perm('main.add_news')):
            from django.http import JsonResponse
            return JsonResponse({'error': 'forbidden'}, status=403)
        return get_shared_media_library_response(request)

    def upload_content_image(self, request):
        if not (request.user.is_staff or request.user.has_perm('main.change_news') or request.user.has_perm('main.add_news')):
            from django.http import JsonResponse
            return JsonResponse({'error': 'forbidden'}, status=403)
        return handle_shared_content_image_upload(request, folder='news/content')

    def toggle_active(self, request, pk):
        from django.http import JsonResponse
        if request.method != 'POST' or not request.user.has_perm('main.change_news'):
            return JsonResponse({'ok': False}, status=403)
        news = News.objects.get(pk=pk)
        news.is_active = not news.is_active
        news.save(update_fields=['is_active'])
        return JsonResponse({'ok': True, 'is_active': news.is_active})

    def changelist_view(self, request, extra_context=None):
        clean_changelist_request_get(self, request)
        extra_context = extra_context or {}
        current_category = request.GET.get('category__id__exact', '')
        cats = []
        for cat in NewsCategory.objects.all():
            cats.append({'obj': cat, 'count': News.objects.filter(category=cat).count()})
        extra_context['news_categories'] = cats
        extra_context['total_count'] = News.objects.count()
        extra_context['current_category'] = current_category
        extra_context['current_is_active'] = request.GET.get('is_active__exact', '')
        response = super().changelist_view(request, extra_context)
        cl = getattr(response, 'context_data', {}).get('cl')
        if cl is not None:
            page = cl.paginator.page(cl.page_num)
            response.context_data['range_start'] = page.start_index()
            response.context_data['range_end'] = page.end_index()
        return response

    @admin.display(description='Tiêu đề')
    def title_with_image(self, obj):
        from django.utils.html import format_html
        style = "color: #007bff; font-size: 11px;"
        thumb = obj.thumbnail_url()
        if thumb:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 10px;">'
                '<img src="{}" style="width: 40px; height: 30px; object-fit: cover; border-radius: 4px;" />'
                '<span style="{}">{}</span>'
                '</div>',
                thumb, style, obj.title
            )
        return format_html('<span style="{}">{}</span>', style, obj.title)


class HomeBannerInline(TabularInline):
    model = HomeBanner
    extra = 1

class PartnerInline(TabularInline):
    model = Partner
    fields = ('image',)
    extra = 1

class AboutGalleryImageInline(TabularInline):
    model = AboutGalleryImage
    fields = ('image', 'image_url', 'caption', 'ratio')
    extra = 1

@admin.register(ThemeSettings)
class ThemeSettingsAdmin(ModelAdmin):
    change_list_template = 'admin/main/themesettings/change_list.html'
    change_form_template = 'admin/main/themesettings/change_form.html'

    inlines = [PartnerInline, AboutGalleryImageInline]

    fieldsets = (
        ('Đầu trang & Logo', {
            'fields': (
                'logo', 'cta_btn_text', 'cta_btn_link',
                'hero_title', 'hero_desc', 'hero_btn_text', 'hero_btn_link', 'hero_video_file', 'hero_video_url',
                'header_text', 'hotline_1', 'hotline_2', 'email', 'open_hours'
            ),
            'classes': ('tab-header',),
        }),
        ('Module Giới thiệu', {
            'fields': ('show_intro', 'intro_badge', 'intro_title', 'intro_description', 'intro_youtube_url'),
            'classes': ('tab-intro',),
        }),
        ('Danh mục sản phẩm', {
            'fields': (
                'show_products', 'products_badge', 'products_title', 'products_btn_text', 'products_btn_link',
                'prod_cat_1_title', 'prod_cat_1_link', 'prod_cat_1_image',
                'prod_cat_2_title', 'prod_cat_2_link', 'prod_cat_2_image',
                'prod_cat_3_title', 'prod_cat_3_link', 'prod_cat_3_image',
                'prod_cat_4_title', 'prod_cat_4_link', 'prod_cat_4_image',
            ),
            'classes': ('tab-products',),
        }),
        ('Phóng sự thực tế', {
            'fields': ('show_phong_su', 'phong_su_badge', 'phong_su_title', 'phong_su_desc', 'phong_su_btn_text', 'phong_su_btn_link'),
            'classes': ('tab-phong-su',),
        }),
        ('Minh chứng chất lượng', {
            'fields': ('show_quality', 'quality_image', 'quality_title', 'quality_description_html', 'quality_drive_link', 'quality_drive_btn_text'),
            'classes': ('tab-quality',),
        }),
        ('Chân trang (Footer)', {
            'fields': (
                'footer_company_name', 'footer_address', 'footer_office_address', 'footer_phone',
                'footer_email', 'footer_media_email',
                'footer_doc_1_title', 'footer_doc_1_link',
                'footer_doc_2_title', 'footer_doc_2_link',
                'footer_doc_3_title', 'footer_doc_3_link',
                'footer_doc_4_title', 'footer_doc_4_link',
                'footer_facebook', 'footer_zalo', 'footer_youtube', 'footer_tiktok', 'footer_linkedin', 'footer_shopee', 'footer_group',
                'footer_map_iframe', 'footer_copyright'
            ),
            'classes': ('tab-footer',),
        }),
        ('Trang Giới thiệu (Về chúng tôi)', {
            'fields': (
                'about_hero_title', 'about_intro_image', 'about_main_heading', 'about_intro_content',
                'about_statement_heading', 'about_statement_col1', 'about_statement_col2',
                'about_story_heading', 'about_story_content', 'about_story_image',
                'about_vision_title', 'about_vision_desc',
                'about_commitment_title', 'about_commitment_desc',
                'about_gallery_title'
            ),
            'classes': ('tab-about',),
        }),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in [
            'intro_description', 'phong_su_desc', 'quality_description_html', 'footer_map_iframe',
            'about_intro_content', 'about_statement_col1', 'about_statement_col2',
            'about_story_content', 'about_vision_desc', 'about_commitment_desc'
        ]:
            kwargs['widget'] = forms.Textarea(attrs={'rows': 5})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


VIETNAM_PROVINCES = [
    'Hà Nội', 'Hồ Chí Minh', 'Hải Phòng', 'Đà Nẵng', 'Cần Thơ',
    'An Giang', 'Bà Rịa - Vũng Tàu', 'Bắc Giang', 'Bắc Kạn', 'Bạc Liêu',
    'Bắc Ninh', 'Bến Tre', 'Bình Định', 'Bình Dương', 'Bình Phước',
    'Bình Thuận', 'Cà Mau', 'Cao Bằng', 'Đắk Lắk', 'Đắk Nông',
    'Điện Biên', 'Đồng Nai', 'Đồng Tháp', 'Gia Lai', 'Hà Giang',
    'Hà Nam', 'Hà Tĩnh', 'Hải Dương', 'Hậu Giang', 'Hòa Bình',
    'Hưng Yên', 'Khánh Hòa', 'Kiên Giang', 'Kon Tum', 'Lai Châu',
    'Lâm Đồng', 'Lạng Sơn', 'Lào Cai', 'Long An', 'Nam Định',
    'Nghệ An', 'Ninh Bình', 'Ninh Thuận', 'Phú Thọ', 'Phú Yên',
    'Quảng Bình', 'Quảng Nam', 'Quảng Ngãi', 'Quảng Ninh', 'Quảng Trị',
    'Sóc Trăng', 'Sơn La', 'Tây Ninh', 'Thái Bình', 'Thái Nguyên',
    'Thanh Hóa', 'Thừa Thiên Huế', 'Tiền Giang', 'Trà Vinh', 'Tuyên Quang',
    'Vĩnh Long', 'Vĩnh Phúc', 'Yên Bái'
]


class DistributorAdminForm(forms.ModelForm):
    province = forms.ChoiceField(
        choices=[('', '-- Chọn tỉnh / thành phố --')] + [(p, p) for p in VIETNAM_PROVINCES],
        label='Tỉnh / Thành phố',
        required=True,
    )

    class Meta:
        model = Distributor
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'VD: CÔNG TY TNHH THIẾT BỊ CÔNG NGHIỆP VÀ VẬT LIỆU XÂY DỰNG TH VIỆT NAM'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'VD: Số 48, phố Chính Trung, xã Gia Lâm, TP Hà Nội hoặc Hà Nội & Bắc Ninh'}),
            'hotline_label': forms.TextInput(attrs={'placeholder': 'VD: HOTLINE TƯ VẤN & MUA HÀNG hoặc LIÊN HỆ MUA HÀNG'}),
            'phone': forms.TextInput(attrs={'placeholder': 'VD: 0982 884 060 / 0866 609 289 hoặc Ms Nguyên: 0865 213 586'}),
            'map_address': forms.TextInput(attrs={'placeholder': 'VD: 48 Phố Chính Trung, Trâu Quỳ, Gia Lâm, Hà Nội'}),
            'google_maps_link': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Dán link Google Maps (VD: https://www.google.com/maps/place/...@10.762,106.660,17z/...) hoặc mã nhúng <iframe src="https://www.google.com/maps/embed?pb=...">'}),
            'email': forms.EmailInput(attrs={'placeholder': 'VD: contact@thvietnam.vn'}),
            'website': forms.URLInput(attrs={'placeholder': 'VD: https://thvietnam.vn'}),
            'youtube_url': forms.URLInput(attrs={'placeholder': 'VD: https://youtube.com/@thvietnam'}),
            'tiktok_url': forms.URLInput(attrs={'placeholder': 'VD: https://tiktok.com/@thvietnam'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'order' in self.fields:
            self.fields['order'].required = False
            self.fields['order'].initial = 0
        if 'hotline_label' in self.fields:
            self.fields['hotline_label'].required = False
        if 'map_address' in self.fields:
            self.fields['map_address'].required = False


class DistributorLinkInlineForm(forms.ModelForm):
    class Meta:
        model = DistributorLink
        fields = ['label', 'url']
        widgets = {
            'label': forms.TextInput(attrs={'placeholder': 'VD: Facebook, Zalo, TikTok...'}),
            'url': forms.TextInput(attrs={'placeholder': 'https://...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'label' in self.fields:
            self.fields['label'].required = False
        if 'url' in self.fields:
            self.fields['url'].required = False


class DistributorLinkInline(TabularInline):
    model = DistributorLink
    form = DistributorLinkInlineForm
    extra = 0
    fields = ['label', 'url']
    show_title = False


@admin.register(Distributor)
class DistributorAdmin(ModelAdmin):
    change_list_template = 'admin/main/distributor/change_list.html'
    change_form_template = 'admin/main/distributor/change_form.html'
    form = DistributorAdminForm
    list_fullwidth = True
    list_display = ['name', 'address_type', 'address', 'province', 'phone', 'is_active', 'order']
    list_filter = ['province', 'address_type', 'is_active']
    search_fields = ['name', 'address', 'phone', 'province']
    ordering = ['province', 'name']
    inlines = [DistributorLinkInline]

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('toggle-active/<int:pk>/', self.admin_site.admin_view(self.toggle_active), name='main_distributor_toggle_active'),
        ]
        return custom_urls + urls

    @staticmethod
    def _resolve_google_maps_link(raw_link):
        """Link rút gọn (maps.app.goo.gl, goo.gl/maps) không thể nhúng trực tiếp vì không chứa toạ độ.
        Server thử theo dõi redirect để lấy link đầy đủ (có toạ độ @lat,lng) rồi lưu lại thay cho link rút gọn."""
        import re
        link = raw_link.strip()
        if '<iframe' in link.lower() or '/maps/embed' in link.lower() or re.search(r'@-?\d+\.\d+,-?\d+\.\d+', link):
            return raw_link
        if not re.search(r'goo\.gl/', link, re.IGNORECASE):
            return raw_link
        try:
            import urllib.request
            req = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                final_url = resp.geturl()
            if final_url and final_url != link:
                return final_url
        except Exception:
            pass
        return raw_link

    def save_model(self, request, obj, form, change):
        if obj.google_maps_link:
            obj.google_maps_link = self._resolve_google_maps_link(obj.google_maps_link)
        super().save_model(request, obj, form, change)

    def toggle_active(self, request, pk):
        from django.http import JsonResponse
        if request.method != 'POST' or not request.user.has_perm('main.change_distributor'):
            return JsonResponse({'ok': False}, status=403)
        try:
            dist = Distributor.objects.get(pk=pk)
            dist.is_active = not dist.is_active
            dist.save(update_fields=['is_active'])
            return JsonResponse({'ok': True, 'is_active': dist.is_active})
        except Distributor.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)

    def changelist_view(self, request, extra_context=None):
        clean_changelist_request_get(self, request)
        extra_context = extra_context or {}
        current_province = request.GET.get('province__exact', '')
        
        # Build province tabs
        prov_list = Distributor.objects.values_list('province', flat=True).distinct()
        tabs = []
        for prov in sorted([p for p in set(prov_list) if p]):
            count = Distributor.objects.filter(province=prov).count()
            tabs.append({'name': prov, 'count': count})

        extra_context['province_tabs'] = tabs
        extra_context['total_count'] = Distributor.objects.count()
        extra_context['current_province'] = current_province
        extra_context['current_is_active'] = request.GET.get('is_active__exact', '')
        response = super().changelist_view(request, extra_context)
        cl = getattr(response, 'context_data', {}).get('cl')
        if cl is not None:
            try:
                page = cl.paginator.page(cl.page_num)
                response.context_data['range_start'] = page.start_index()
                response.context_data['range_end'] = page.end_index()
            except Exception:
                pass
        return response

