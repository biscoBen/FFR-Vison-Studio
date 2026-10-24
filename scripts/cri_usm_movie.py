"""Normalize our movie USM to the native movie's chunk/seek conventions.

No video data is decoded or changed. This is deliberately limited to one
unencrypted VP9 channel, matching opacity and a native stereo ADX soundtrack. It must never be
used to rewrite arbitrary game movies.
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


def pack_chunks(items):
    result = bytearray()
    for c in items:
        header, payload = bytearray(c['header']), c['payload']
        size = max(2048 if c['type'] == b'CRID' else 0, (len(header)+len(payload)+31)//32*32)
        padding = size-len(header)-len(payload)
        struct.pack_into('>I', header, 4, size-8)
        struct.pack_into('>H', header, 10, padding)
        result.extend(header); result.extend(payload); result.extend(bytes(padding))
    return bytes(result)


def normalize(raw, *, opaque_alpha=False, soundtrack=False):
    items = chunks(raw)
    kinds = (b'CRID', b'@SFV', b'@ALP') if opaque_alpha else (b'CRID', b'@SFV')
    if soundtrack: kinds += (b'@SFA',)
    if any(c['type'] not in kinds or c['channel'] != 0 for c in items):
        raise ValueError('Only our video-only or explicitly enabled soundtrack channel-zero movie is supported')
    position = 0
    for c in items:
        size = len(c['header']) + len(c['payload'])
        # Retain the native 2 KiB CRID header reservation; align every chunk to 32.
        c['size'] = max(2048 if c['type'] == b'CRID' else 0, (size+31)//32*32)
        c['position'] = position; position += c['size']
    reports = {}
    for kind, codec in [(b'@SFV', 9)] + ([(b'@ALP', 1)] if opaque_alpha else []):
        streams = [c for c in items if c['type'] == kind and c['kind'] == 0]
        metadata = [c for c in items if c['type'] == kind and c['kind'] == 3]
        headers = [c for c in items if c['type'] == kind and c['kind'] == 1]
        if len(headers) != 1 or not streams or not metadata:
            raise ValueError('Expected one video header, packets and seek metadata per channel')
        header = headers[0]['payload']; row, = integer_rows(header)
        if value(header, row, 'mpeg_codec') != codec or value(header, row, 'total_frames') != len(streams):
            raise ValueError('Expected one complete packet per movie frame')
        if kind == b'@ALP' and (value(header, row, 'alpha_type') != 1
                or len(streams) != reports[b'@SFV']['packets']):
            raise ValueError('Opacity channel must match the complete color movie')
        maximum = max(c['size'] for c in streams)
        put(header, row, 'metadata_size', sum(c['size'] for c in metadata))
        put(header, row, 'ixsize', maximum)
        for c in metadata:
            for seek in integer_rows(c['payload']):
                frame = value(c['payload'], seek, 'ofs_frmid')
                if not 0 <= frame < len(streams): raise ValueError('Invalid movie seek frame')
                put(c['payload'], seek, 'ofs_byte', streams[frame]['position'])
        reports[kind] = {'packets': len(streams), 'max': maximum,
                         'metadata': sum(c['size'] for c in metadata)}
    crid = items[0]['payload']
    for row in integer_rows(crid):
        if value(crid, row, 'stmid') == 0:
            put(crid, row, 'filesize', position)
    result = pack_chunks(items)
    return result, {'containerBytes':len(result), 'videoPackets':reports[b'@SFV']['packets'],
                           'alphaPackets':reports.get(b'@ALP', {}).get('packets', 0),
                           'metadataChunkBytes':sum(r['metadata'] for r in reports.values()),
                           'maxPictureDataSize':max(r['max'] for r in reports.values()), 'chunkAlignment':32}


def without_soundtrack(raw):
    """Remove just the audio stream before rescoring; preserve color and opacity."""
    from wannacri.usm.page import get_pages, pack_pages
    parts = chunks(raw)
    pages = get_pages(parts[0]['payload'])
    parts[0]['payload'] = bytearray(pack_pages([
        p for p in pages if p['stmid'].val != int.from_bytes(b'@SFA', 'big')], 'UTF-8'))
    return normalize(pack_chunks([p for p in parts if p['type'] != b'@SFA']), opaque_alpha=True)[0]


def native_adx(adx):
    """Validate stereo ADX v4 and use the native movie's 288-byte header layout."""
    if (len(adx) < 40 or adx[:2] != b'\x80\x00'
            or adx[4:8] != bytes((3,18,4,2)) or adx[18:20] != bytes((4,0))):
        raise ValueError('Expected unencrypted stereo ADX v4 with 18-byte blocks')
    header = int.from_bytes(adx[2:4], 'big') + 4
    rate, samples = struct.unpack_from('>II', adx, 8)
    body_bytes = ((samples+31)//32)*18*2
    if (rate, samples) != (48000,307200) or adx[header-6:header] != b'(c)CRI':
        raise ValueError('Expected the complete 48-kHz 6.4-second ADX score')
    if len(adx) != header+body_bytes+18 or adx[-18:-14] != b'\x80\x01\x00\x0e':
        raise ValueError('ADX size or end marker does not match its sample count')
    # Native Cloud's header packet is 288 bytes, including the v4 histories and
    # padding before the copyright marker. Padding is not compressed audio.
    result = bytearray(adx[:32]);result[2:4] = (284).to_bytes(2,'big')
    result.extend(bytes(282-len(result)));result.extend(b'(c)CRI')
    result.extend(adx[header:])
    return bytes(result)


def with_soundtrack(raw, adx):
    """Mux the native movie's stereo ADX layout, without changing any picture.

    Every 30-fps data packet contains 1,600 samples: fifty 32-sample ADX groups,
    with the two 18-byte channel blocks kept together. HCA is deliberately not
    accepted here after it produced garbled audio in the game despite clean
    offline decoding. Movie metadata and the actual codec must agree.
    """
    from wannacri.usm.page import get_pages, pack_pages, UsmPage
    from wannacri.usm.types import ElementType as T
    import hashlib
    adx = native_adx(adx)
    rate, samples, channels, header_size = 48000,307200,2,288
    parts = chunks(raw)
    if any(c['type'] not in (b'CRID', b'@SFV', b'@ALP') or c['channel'] != 0 for c in parts):
        raise ValueError('Expected one silent color/opacity movie')
    pages = get_pages(parts[0]['payload'])
    audio = UsmPage('CRIUSF_DIR_STREAM')
    for name, typ, val in [('fmtver',T.I32,pages[0]['fmtver'].val), ('filename',T.STRING,'score.adx'),
            ('filesize',T.I32,len(adx)), ('datasize',T.I32,0), ('stmid',T.I32,int.from_bytes(b'@SFA','big')),
            ('chno',T.I16,0), ('minchk',T.I16,1), ('minbuf',T.I32,27860),
            ('avbps',T.I32,round(len(adx)*8/(samples/rate)))]:
        audio.update(name, typ, val)
    parts[0]['payload'] = bytearray(pack_pages([*pages,audio], 'UTF-8'))
    info = UsmPage('AUDIO_HDRINFO')
    for name, typ, val in [('audio_codec',T.I8,2), ('sampling_rate',T.I32,rate),
            ('total_samples',T.I32,samples), ('num_channels',T.I32,channels),
            ('metadata_count',T.I32,0), ('metadata_size',T.I32,0), ('ixsize',T.I32,27860),
            ('ambisonics',T.I8,0), ('channel_config',T.I32,0)]:
        info.update(name, typ, val)
    def chunk(kind, payload, tick=0):
        item_header = bytearray(32);item_header[:4] = b'@SFA';item_header[9] = 24;item_header[15] = kind
        struct.pack_into('>II', item_header, 16, tick, 2997)
        return {'type':b'@SFA','kind':kind,'channel':0,'header':item_header,'payload':payload}
    first_end = next(i for i,p in enumerate(parts) if p['kind']==2)
    parts.insert(first_end, chunk(1,pack_pages([info],'UTF-8')))
    metadata = next(i for i,p in enumerate(parts) if p['kind']==3)
    parts.insert(metadata, chunk(2,b'#HEADER END     ===============\0'))
    first_data = next(i for i,p in enumerate(parts) if p['kind']==0)
    prefix, stream = parts[:first_data], parts[first_data:]
    audio_packets = [chunk(0,adx[:header_size])]
    body=adx[header_size:-18]
    for index in range(192):
        audio_packets.append(chunk(0,body[index*1800:(index+1)*1800],index*999//10))
    audio_packets.append(chunk(0,adx[-18:],192*999//10))
    media = [p for p in stream if p['kind']==0] + audio_packets
    media.sort(key=lambda p: struct.unpack_from('>I',p['header'],16)[0] /
               struct.unpack_from('>I',p['header'],20)[0])
    ending = [p for p in stream if p['kind']!=0]
    ending.append(chunk(2,b'#CONTENTS END   ===============\0'))
    result, report = normalize(pack_chunks([*prefix,*media,*ending]), opaque_alpha=True, soundtrack=True)
    return result, {**report, 'audioPackets':len(audio_packets), 'audioSamples':samples,
                    'audioSha256':hashlib.sha256(adx).hexdigest()}


def with_opaque_alpha(raw, fixture):
    """Mux our 1080p VP9 movie with a native constant-white Sofdec I-frame.

    No proprietary codec is guessed or relabelled. Every alpha picture is the
    same independently decodable native opacity frame; color packets remain
    byte-identical. WannaCRI is needed only by this developer packaging step.
    """
    import copy
    import hashlib
    import json
    from pathlib import Path
    from wannacri.usm.page import get_pages, pack_pages
    from wannacri.usm.types import ElementType
    fixture = Path(fixture)
    provenance = json.loads((fixture / 'provenance.json').read_text())
    alpha_header = bytearray((fixture / 'header.bin').read_bytes())
    alpha_frame = (fixture / 'frame.m2v').read_bytes()
    for name, data in [('header', alpha_header), ('frame', alpha_frame)]:
        if hashlib.sha256(data).hexdigest() != provenance[name + 'Sha256']:
            raise ValueError('Native opacity fixture checksum mismatch')
    parts = chunks(raw)
    if any(c['type'] not in (b'CRID', b'@SFV') or c['channel'] != 0 for c in parts):
        raise ValueError('Expected our single-color VP9 movie')
    color_header, = [c for c in parts if c['type'] == b'@SFV' and c['kind'] == 1]
    row, = integer_rows(color_header['payload'])
    if tuple(value(color_header['payload'], row, k) for k in ('width', 'height', 'mpeg_codec')) != (1920, 1080, 9):
        raise ValueError('Native opacity frame requires 1920x1080 VP9 color')
    streams = [c for c in parts if c['type'] == b'@SFV' and c['kind'] == 0]
    alpha_row, = integer_rows(alpha_header)
    put(alpha_header, alpha_row, 'total_frames', len(streams))
    pages = get_pages(parts[0]['payload'])
    color, = [p for p in pages if p['stmid'].val == int.from_bytes(b'@SFV', 'big')]
    alpha = copy.deepcopy(color)
    alpha.update('filename', ElementType.STRING, 'studio-opaque-alpha.sfv')
    alpha.update('stmid', ElementType.I32, int.from_bytes(b'@ALP', 'big'))
    alpha.update('filesize', ElementType.I32, len(alpha_frame) * len(streams))
    alpha.update('minbuf', ElementType.I32, len(alpha_frame) + 32)
    alpha.update('avbps', ElementType.I32, len(alpha_frame) * 30 * 8)
    parts[0]['payload'] = bytearray(pack_pages([*pages, alpha], 'UTF-8'))
    combined = []
    for part in parts:
        combined.append(part)
        if part['type'] != b'@SFV': continue
        extra = copy.deepcopy(part)
        extra['type'] = b'@ALP'; extra['header'][:4] = b'@ALP'
        if part['kind'] == 1: extra['payload'] = alpha_header
        elif part['kind'] == 0: extra['payload'] = bytearray(alpha_frame)
        combined.append(extra)
    # Repack lengths before normalize() resolves the two seek tables against
    # their final interleaved positions. No frame data is decoded here.
    result = bytearray()
    for part in combined:
        header, data = part['header'], part['payload']
        size = max(2048 if part['type'] == b'CRID' else 0, (len(header) + len(data) + 31) // 32 * 32)
        padding = size - len(header) - len(data)
        struct.pack_into('>I', header, 4, size - 8)
        struct.pack_into('>H', header, 10, padding)
        result.extend(header); result.extend(data); result.extend(bytes(padding))
    return normalize(bytes(result), opaque_alpha=True)
