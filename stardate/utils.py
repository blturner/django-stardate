import copy

from dateutil.parser import parse


def prepare_bits(metadata, parent=None):
    bits = copy.copy(metadata)
    try:
        bits.pop('contents')
    except:
        pass
    try:
        bits['modified'] = parse(bits.get('modified'))
        bits['client_mtime'] = parse(bits.get('client_mtime'))
    except:
        pass
    if parent:
        bits['folder'] = parent
    return bits
