import copy

from datetime import datetime, timedelta

TIMEFORMAT = "%a, %d %b %Y %H:%M:%S"


def format_timestamp(string, format):
    timestamp = string[:-6]
    offset = int(string[-5:])
    delta = timedelta(hours=offset / 100)
    d = datetime.strptime(timestamp, format)
    d -= delta
    return d


def prepare_bits(metadata, parent=None):
    bits = copy.copy(metadata)
    try:
        bits.pop('contents')
    except:
        pass
    try:
        bits['modified'] = format_timestamp(bits.get('modified'), TIMEFORMAT)
        bits['client_mtime'] = format_timestamp(bits.get('client_mtime'), TIMEFORMAT)
    except:
        pass
    if parent:
        bits['folder'] = parent
    return bits
