import copy

from dateutil.parser import parse
from django.utils import timezone

TZ = timezone.get_default_timezone()


def prepare_bits(metadata, parent=None):
    bits = copy.copy(metadata)
    try:
        bits.pop('contents')
    except:
        pass
    try:
        bits['modified'] = timezone.make_aware(parse(bits.get('modified')), TZ)
        bits['client_mtime'] = timezone.make_aware(parse(bits.get('client_mtime')), TZ)
    except:
        pass
    if parent:
        bits['folder'] = parent
    return bits
