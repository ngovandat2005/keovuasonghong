import io
import os
from PIL import Image
from django.core.files.base import ContentFile
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Product, ProductImage, News, Project, Banner, ThemeSettings


def convert_image_field_to_webp(field_file):
    """Tự động nén và chuyển đổi ImageField sang .webp trước khi lưu lên Cloudinary/Storage."""
    if not field_file or not hasattr(field_file, 'file'):
        return
    filename = field_file.name
    if not filename or filename.lower().endswith('.webp'):
        return

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        return

    try:
        field_file.open()
        img = Image.open(field_file)
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')

        buf = io.BytesIO()
        img.save(buf, format='WEBP', quality=85, method=6)
        new_name = os.path.splitext(filename)[0] + '.webp'
        field_file.save(new_name, ContentFile(buf.getvalue()), save=False)
    except Exception:
        pass


@receiver(pre_save, sender=Product)
def product_webp_converter(sender, instance, **kwargs):
    if instance.image:
        convert_image_field_to_webp(instance.image)


@receiver(pre_save, sender=ProductImage)
def product_image_webp_converter(sender, instance, **kwargs):
    if instance.image:
        convert_image_field_to_webp(instance.image)


@receiver(pre_save, sender=News)
def news_webp_converter(sender, instance, **kwargs):
    if instance.image:
        convert_image_field_to_webp(instance.image)


@receiver(pre_save, sender=Project)
def project_webp_converter(sender, instance, **kwargs):
    if instance.image:
        convert_image_field_to_webp(instance.image)


@receiver(pre_save, sender=Banner)
def banner_webp_converter(sender, instance, **kwargs):
    if instance.image:
        convert_image_field_to_webp(instance.image)


@receiver(pre_save, sender=ThemeSettings)
def theme_settings_webp_converter(sender, instance, **kwargs):
    for f in [
        'logo', 'prod_cat_1_image', 'prod_cat_2_image', 'prod_cat_3_image',
        'prod_cat_4_image', 'quality_image', 'about_intro_image', 'about_story_image'
    ]:
        field_val = getattr(instance, f, None)
        if field_val:
            convert_image_field_to_webp(field_val)
