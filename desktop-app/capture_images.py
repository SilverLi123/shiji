"""Bounded structural image validation before publishing a website cover.

No third-party decoder. PNG validates CRC, deflate length and scanline filters;
JPEG/GIF/WebP validate their containers/dimensions, not full pixel decoding.
The existing renderer still falls back to a poster on decode failure.
"""
import struct
import zlib

MAX_IMAGE = 5 * 1024 * 1024
MAX_PIXELS = 16_000_000


def dimensions(w, h):
    if not 0 < w <= 16384 or not 0 < h <= 16384 or w * h > MAX_PIXELS:
        raise ValueError('图片尺寸无效或过大。')


def png(data):
    pos, image, header, ended = 8, [], None, False
    while pos + 12 <= len(data):
        size, = struct.unpack_from('>I', data, pos)
        name, payload = data[pos+4:pos+8], data[pos+8:pos+8+size]
        if pos + 12 + size > len(data) or zlib.crc32(name + payload) & 0xffffffff != struct.unpack_from('>I', data, pos+8+size)[0]:
            raise ValueError('PNG 校验失败。')
        if name == b'IHDR':
            if header is not None or pos != 8 or size != 13:
                raise ValueError('PNG 头无效。')
            header = struct.unpack('>IIBBBBB', payload)
        elif name == b'IDAT':
            image.append(payload)
        elif name == b'IEND':
            ended = size == 0 and pos+12 == len(data)
            break
        pos += size + 12
    if not header or not ended or not image:
        raise ValueError('PNG 文件不完整。')
    w, h, depth, color, compression, filtering, interlace = header
    dimensions(w, h)
    depths = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
    if depth not in depths.get(color, ()) or compression or filtering or interlace not in (0, 1):
        raise ValueError('PNG 编码无效。')
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    passes = [(0, 0, 1, 1)] if not interlace else [(0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2)]
    rows = []
    for x, y, dx, dy in passes:
        width, height = max(0, (w-x+dx-1)//dx), max(0, (h-y+dy-1)//dy)
        if width and height:
            rows.extend([1+(width*channels*depth+7)//8] * height)
    expected, count, row, offset = sum(rows), 0, 0, 0
    decoder = zlib.decompressobj()
    for segment in image:
        for start in range(0, len(segment), 4096):
            pending = segment[start:start+4096]
            while pending:
                raw = decoder.decompress(pending, min(65536, expected-count+1))
                pending = decoder.unconsumed_tail
                count += len(raw)
                if count > expected:
                    raise ValueError('PNG 展开大小无效。')
                cursor = 0
                while cursor < len(raw):
                    if row >= len(rows) or (offset == 0 and raw[cursor] > 4):
                        raise ValueError('PNG 像素行无效。')
                    take = min(len(raw)-cursor, rows[row]-offset)
                    cursor += take
                    offset += take
                    if offset == rows[row]:
                        row, offset = row+1, 0
    if not decoder.eof or decoder.unused_data or count != expected:
        raise ValueError('PNG 压缩流不完整。')


def jpeg(data):
    pos, sized, scanned = 2, False, False
    while pos < len(data):
        if data[pos] != 255:
            raise ValueError('JPEG 标记无效。')
        while pos < len(data) and data[pos] == 255:
            pos += 1
        if pos >= len(data):
            break
        marker = data[pos]
        pos += 1
        if marker == 0xd9:
            if sized and scanned and pos == len(data):
                return
            break
        if pos+2 > len(data):
            break
        size = int.from_bytes(data[pos:pos+2], 'big')
        if size < 2 or pos+size > len(data):
            break
        if marker in (0xc0, 0xc1, 0xc2):
            if size < 8 or data[pos+2] != 8:
                break
            h, w = struct.unpack_from('>HH', data, pos+3)
            dimensions(w, h)
            sized = True
        pos += size
        if marker == 0xda:
            scanned = True
            while pos < len(data):
                pos = data.find(b'\xff', pos)
                if pos < 0 or pos+1 >= len(data):
                    raise ValueError('JPEG 数据不完整。')
                if data[pos+1] == 0 or 0xd0 <= data[pos+1] <= 0xd7:
                    pos += 2
                    continue
                break
    raise ValueError('JPEG 文件不完整或编码不支持。')


def gif(data):
    if len(data) < 14:
        raise ValueError('GIF 数据不完整。')
    w, h = struct.unpack_from('<HH', data, 6)
    dimensions(w, h)
    pos = 13 + (3 * (2 ** ((data[10] & 7)+1)) if data[10] & 128 else 0)
    frames, pixels = 0, 0
    while pos < len(data):
        tag = data[pos]
        pos += 1
        if tag == 0x3b and frames and pos == len(data):
            return
        if tag == 0x21:
            pos += 1
        elif tag == 0x2c and pos+9 <= len(data):
            x, y, fw, fh, flags = struct.unpack_from('<HHHHB', data, pos)
            dimensions(fw, fh)
            pixels += fw*fh
            if x+fw > w or y+fh > h or pixels > MAX_PIXELS*2:
                break
            pos += 9 + (3 * (2 ** ((flags & 7)+1)) if flags & 128 else 0) + 1
            frames += 1
        else:
            break
        while pos < len(data) and data[pos]:
            pos += data[pos]+1
        pos += 1
    raise ValueError('GIF 文件不完整。')


def webp(data):
    if len(data) < 20 or int.from_bytes(data[4:8], 'little')+8 != len(data):
        raise ValueError('WebP 文件不完整。')
    pos, sized, frame = 12, False, False
    while pos+8 <= len(data):
        tag, size = data[pos:pos+4], int.from_bytes(data[pos+4:pos+8], 'little')
        chunk = data[pos+8:pos+8+size]
        if len(chunk) != size:
            break
        if tag == b'VP8X' and size == 10:
            dimensions(int.from_bytes(chunk[4:7], 'little')+1, int.from_bytes(chunk[7:10], 'little')+1)
            sized = True
        elif tag == b'VP8 ' and size >= 10 and chunk[3:6] == b'\x9d\x01\x2a':
            w, h = struct.unpack_from('<HH', chunk, 6)
            dimensions(w & 16383, h & 16383)
            sized, frame = True, True
        elif tag == b'VP8L' and size >= 5 and chunk[0] == 0x2f:
            bits = int.from_bytes(chunk[1:5], 'little')
            dimensions((bits & 16383)+1, ((bits >> 14) & 16383)+1)
            sized, frame = True, True
        pos += 8+size+(size & 1)
    if not sized or not frame or pos != len(data):
        raise ValueError('WebP 编码不支持或无图像帧。')


def validate_image(data, content_type):
    from storage import detect_mime
    if not data or len(data) > MAX_IMAGE:
        raise ValueError('图片为空或超过 5 MB。')
    mime = detect_mime(data)
    supplied = content_type.split(';', 1)[0].strip().lower()
    if supplied == 'image/jpg':
        supplied = 'image/jpeg'
    validators = {'image/png': png, 'image/jpeg': jpeg, 'image/gif': gif, 'image/webp': webp}
    if supplied != mime or mime not in validators:
        raise ValueError('图片声明类型与实际文件不一致。')
    try:
        validators[mime](data)
    except (struct.error, zlib.error, IndexError, OverflowError) as e:
        raise ValueError('图片文件无法验证。') from e
    return mime
