"""Normalize our video-only USM to the native movie's chunk/seek conventions.

No video data is decoded or changed. This is deliberately limited to one
unencrypted VP9 channel; it must never be used to rewrite arbitrary game movies.
"""
import struct


def chunks(raw):
    result = []
    position = 0
    while position < len(raw):
        if position + 32 > len(raw):
            raise ValueError('Truncated USM chunk header')
        size = int.from_bytes(raw[position+4:position+8], 'big') + 8
        start = 8 + raw[position+9]
        padding = int.from_bytes(raw[position+10:position+12], 'big')
        if size < 32 or position + size > len(raw) or not 32 <= start <= size-padding:
            raise ValueError('Invalid USM chunk bounds')
        header = bytearray(raw[position:position+start])
        payload = bytearray(raw[position+start:position+size-padding])
        result.append({'position': position, 'size': size, 'header': header, 'payload': payload,
                       'type': bytes(header[:4]), 'kind': header[15] & 3, 'channel': header[12]})
        position += size
    if not result or result[0]['type'] != b'CRID':
        raise ValueError('Expected CRI USM movie')
    return result


def integer_rows(payload):
    """Return named integer cells as (byte offset, struct format), preserving UTF layout."""
    if payload[:4] != b'@UTF' or len(payload) < 32:
        raise ValueError('Expected CRI UTF table')
    version, rowoff, stroff, dataoff, nameoff, columns, stride, count = struct.unpack_from('>HHIIIHHI', payload, 8)
    if version or 8 + dataoff > len(payload) or count > 100000:
        raise ValueError('Unsupported UTF table')
    strings = payload[8+stroff:8+dataoff]
    sizes = {0:1, 1:1, 2:2, 3:2, 4:4, 5:4, 6:8, 7:8, 8:4, 9:8, 10:4, 11:8}
    formats = {0:'>B', 1:'>b', 2:'>H', 3:'>h', 4:'>I', 5:'>i', 6:'>Q', 7:'>q'}
    cols = []; position = 32
    for _ in range(columns):
        flags = payload[position]; name = struct.unpack_from('>I', payload, position+1)[0]; position += 5
        typ, storage = flags & 15, flags & 240
        if typ not in sizes or storage not in (0x10, 0x30, 0x50):
            raise ValueError('Unsupported UTF cell')
        key = strings[name:strings.index(0, name)].decode('utf-8')
        constant = position if storage == 0x30 else None
        if constant is not None: position += sizes[typ]
        cols.append((key, typ, storage, constant))
    rows = []
    for row in range(count):
        position = 8 + rowoff + row*stride; cells = {}
        for name, typ, storage, constant in cols:
            cell = position if storage == 0x50 else constant
            if typ in formats and cell is not None:
                if cell + sizes[typ] > len(payload): raise ValueError('UTF cell exceeds table')
                cells[name] = (cell, formats[typ])
            if storage == 0x50: position += sizes[typ]
        rows.append(cells)
    return rows


def value(payload, row, name):
    position, fmt = row[name]
    return struct.unpack_from(fmt, payload, position)[0]


def put(payload, row, name, number):
    position, fmt = row[name]
    struct.pack_into(fmt, payload, position, number)


def normalize(raw):
    items = chunks(raw)
    if any(c['type'] not in (b'CRID', b'@SFV') or c['channel'] != 0 for c in items):
        raise ValueError('Only our video-only channel-zero movie is supported')
    position = 0
    for c in items:
        size = len(c['header']) + len(c['payload'])
        # Retain the native 2 KiB CRID header reservation; align every chunk to 32.
        c['size'] = max(2048 if c['type'] == b'CRID' else 0, (size+31)//32*32)
        c['position'] = position; position += c['size']
    streams = [c for c in items if c['type'] == b'@SFV' and c['kind'] == 0]
    metadata = [c for c in items if c['type'] == b'@SFV' and c['kind'] == 3]
    headers = [c for c in items if c['type'] == b'@SFV' and c['kind'] == 1]
    if len(headers) != 1 or not streams or not metadata:
        raise ValueError('Expected one video header, packets and seek metadata')
    header = headers[0]['payload']; row, = integer_rows(header)
    if value(header, row, 'mpeg_codec') != 9 or value(header, row, 'total_frames') != len(streams):
        raise ValueError('Expected one complete VP9 packet per movie frame')
    maximum = max(c['size'] for c in streams)
    put(header, row, 'metadata_size', sum(c['size'] for c in metadata))
    put(header, row, 'ixsize', maximum)
    for c in metadata:
        for row in integer_rows(c['payload']):
            frame = value(c['payload'], row, 'ofs_frmid')
            if not 0 <= frame < len(streams): raise ValueError('Invalid movie seek frame')
            put(c['payload'], row, 'ofs_byte', streams[frame]['position'])
    crid = items[0]['payload']
    for row in integer_rows(crid):
        if value(crid, row, 'stmid') == 0:
            put(crid, row, 'filesize', position)
    result = bytearray()
    for c in items:
        header, payload = c['header'], c['payload']
        padding = c['size']-len(header)-len(payload)
        struct.pack_into('>I', header, 4, c['size']-8)
        struct.pack_into('>H', header, 10, padding)
        result.extend(header); result.extend(payload); result.extend(bytes(padding))
    return bytes(result), {'containerBytes':len(result), 'videoPackets':len(streams),
                           'metadataChunkBytes':sum(c['size'] for c in metadata),
                           'maxPictureDataSize':maximum, 'chunkAlignment':32}
