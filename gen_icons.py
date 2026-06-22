import struct, zlib

def make_png(size):
    bg = (13, 13, 26)
    pixels = bytearray(size * size * 3)
    for i in range(size * size):
        pixels[i*3:i*3+3] = bg

    cs  = size // 5
    gap = max(1, cs // 10)
    ox  = (size - 3 * cs) // 2
    oy  = (size - 2 * cs) // 2

    def fill(x, y, w, h, c):
        for py in range(max(0,y), min(size, y+h)):
            for px in range(max(0,x), min(size, x+w)):
                pixels[(py*size+px)*3:(py*size+px)*3+3] = c

    def cell(col, row, color):
        x = ox + col*cs + gap
        y = oy + row*cs + gap
        s = cs - 2*gap
        bev = max(2, s//12)
        fill(x, y, s, s, color)
        hi = tuple(min(255, v+70) for v in color)
        sh = tuple(max(0,  v-55) for v in color)
        fill(x,     y,     s,   bev, hi)
        fill(x,     y,     bev, s,   hi)
        fill(x,     y+s-bev, s, bev, sh)
        fill(x+s-bev, y,   bev, s,   sh)

    # T-tetromino: .#. / ###
    cell(1, 0, (0,   220, 240))
    cell(0, 1, (0,   200, 255))
    cell(1, 1, (180,   0, 230))
    cell(2, 1, (230, 100,   0))

    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    raw = b''
    for row in range(size):
        raw += b'\x00'
        for col in range(size):
            b = (row*size+col)*3
            raw += bytes(pixels[b:b+3])

    return (b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(raw, 6))
        + chunk(b'IEND', b''))

for size, name in [(192, 'icon-192.png'), (512, 'icon-512.png')]:
    with open(f'/home/user/PP4Rocks/{name}', 'wb') as f:
        f.write(make_png(size))
    print(f'Created {name}')
