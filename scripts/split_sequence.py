"""Losslessly crop a generated RGB PNG contact sheet into four RGB frames.

Usage: python3 scripts/split_sequence.py figures/t2v-follow-targets-sheet.png t2v
Only the Python standard library is needed; no pixels or lettering are synthesized.
"""
import argparse
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
SIGNATURE = b'\x89PNG\r\n\x1a\n'


def paeth(a, b, c):
    p = a + b - c
    distances = abs(p - a), abs(p - b), abs(p - c)
    return (a, b, c)[distances.index(min(distances))]


def read_rgb(path):
    data = path.read_bytes()
    assert data.startswith(SIGNATURE), 'Expected PNG'
    offset, compressed, header = 8, bytearray(), None
    while offset < len(data):
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        body = data[offset + 8:offset + 8 + length]
        crc = struct.unpack('>I', data[offset + 8 + length:offset + 12 + length])[0]
        assert zlib.crc32(kind + body) & 0xffffffff == crc, 'PNG checksum mismatch'
        if kind == b'IHDR':
            header = struct.unpack('>IIBBBBB', body)
        elif kind == b'IDAT':
            compressed.extend(body)
        offset += length + 12
    assert header and header[2:] == (8, 2, 0, 0, 0), 'Expected non-interlaced 8-bit RGB PNG'
    width, height = header[:2]
    stride = width * 3
    raw = zlib.decompress(compressed)
    assert len(raw) == height * (stride + 1)
    previous = bytearray(stride)
    rows = []
    for y in range(height):
        start = y * (stride + 1)
        mode = raw[start]
        row = bytearray(raw[start + 1:start + 1 + stride])
        assert mode in range(5)
        if mode:
            for x in range(stride):
                a, b, c = (row[x - 3] if x >= 3 else 0), previous[x], (previous[x - 3] if x >= 3 else 0)
                predictor = a if mode == 1 else b if mode == 2 else (a + b) // 2 if mode == 3 else paeth(a, b, c)
                row[x] = (row[x] + predictor) & 255
        rows.append(bytes(row))
        previous = row
    return width, height, rows


def chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)


def save_rgb(output, width, height, rows):
    png = SIGNATURE + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(b''.join(b'\x00' + row for row in rows), 9)) + chunk(b'IEND', b'')
    output.write_bytes(png)


def resize_half(source, output):
    """Box-filter 2x downsampling; no retouching or text replacement."""
    width, height, rows = read_rgb(source)
    assert width % 2 == height % 2 == 0
    resized = []
    for y in range(0, height, 2):
        row = bytearray()
        for x in range(0, width * 3, 6):
            for channel in range(3):
                row.append((rows[y][x + channel] + rows[y][x + 3 + channel] + rows[y + 1][x + channel] + rows[y + 1][x + 3 + channel] + 2) // 4)
        resized.append(bytes(row))
    save_rgb(output, width // 2, height // 2, resized)


def split(source, track):
    width, height, rows = read_rgb(source)
    assert width % 2 == height % 2 == 0
    fw, fh = width // 2, height // 2
    dest = ROOT / 'assets/images/sequences'
    dest.mkdir(parents=True, exist_ok=True)
    for index in range(4):
        x, y = (index % 2) * fw, (index // 2) * fh
        output = dest / f'{track}-follow-{index}.png'
        save_rgb(output, fw, fh, [row[x * 3:(x + fw) * 3] for row in rows[y:y + fh]])
        print(f'{output.relative_to(ROOT)}: {fw} x {fh}, RGB')
    corrected = ROOT / 'figures/ref2v-follow-first-frame.png'
    if track == 'ref2v' and corrected.exists():
        resize_half(corrected, dest / 'ref2v-follow-0.png')
        print('Ref2V 0.0 s uses the separately generated correct-spelling first frame.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('track', choices=['t2v', 'ref2v'])
    args = parser.parse_args()
    split(args.source, args.track)
