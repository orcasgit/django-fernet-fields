import django


DJANGO_VERSION = django.get_version().split('.')
if DJANGO_VERSION[0] < "3":
    from django.utils.encoding import force_text
else:
    from django.utils.encoding import force_str as force_text
