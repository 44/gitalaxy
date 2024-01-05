from PIL import Image, ImageDraw
import math
import os
from hashlib import blake2b

skipped_lines=0
def read_history(fname):
    global skipped_lines
    events = dict()
    with open(fname, 'r') as f:
        lines = [l.strip() for l in f.readlines()]
        for l in lines:
            if l.startswith('20'):
                i = l.index(' ')
                if i == -1:
                    skipped_lines += 1
                    continue
                d = l[0:i].strip()
                source = l[i+1:].strip()
                if d in events:
                    events[d].append(source)
                else:
                    events[d] = [source]
            else:
                skipped_lines += 1
                print(l)
                continue
    return events

from dataclasses import dataclass

@dataclass
class Constellation:
    x: int
    y: int
    scale: float
    stars: set

@dataclass
class Star:
    x: int
    y: int
    brightness: int
    color: tuple

@dataclass
class Projection:
    x: int
    y: int
    c: tuple
    s: int

class Sky:
    def __init__(self):
        self.scales = dict()
        self.stars = dict()
        self.max_brightness = 0
        self.brightest = ''
    def update(self, dname, fname):
        if dname in self.scales:
            self.scales[dname].stars.add(fname)
            nstars = len(self.scales[dname].stars)
            if nstars > 1:
                self.scales[dname].scale = math.log(nstars, 2)
            else:
                self.scales[dname].scale = 1
        else:
            h = blake2b(digest_size=4)
            h.update(bytes(dname, 'utf-8'))
            d = h.digest()
            x = d[0]*256 + d[1]
            y = d[2]*256 + d[3]
            self.scales[dname] = Constellation(x, y, 1, set([fname]))
    def advance(self, changes):
        # decay
        for fname in sorted(self.stars.keys()):
            s = self.stars[fname]
            if s.brightness == 10:
                pass
                # del self.stars[fname]
            else:
                s.brightness = s.brightness - 1
        for change in changes:
            dname = os.path.dirname(change)
            fname = os.path.basename(change)
            if fname in self.stars:
                nb = self.stars[fname].brightness + 10
                self.stars[fname].brightness = nb
                if nb > self.max_brightness:
                    self.max_brightness = nb
                    self.brightest = fname
            else:
                x, y = self.get_position(dname, fname)
                self.stars[fname] = Star(x=x, y=y, brightness=80, color=self.get_color(fname))

    def get_position(self, dname, fname):
        cnst = self.scales[dname]
        hn = blake2b(digest_size=2)
        hn.update(bytes(fname, 'utf-8'))
        dn = hn.digest()
        dist = dn[0] * dn[0] / 256 * cnst.scale * 3
        angle = dn[1]
        x = cnst.x + dist * math.cos(angle)
        y = cnst.y + dist * math.sin(angle)
        return (x, y)

    def get_color(self, fname):
        color = (127, 127, 255)
        if "test" in fname.lower():
            color = (127, 255, 255)
        if fname.endswith('.cs'):
            color = (255, 127, 127)
        if fname.endswith('.h'):
            color = (255, 255, 255)
        return color
    def project(self, s, w, h):
        x = int(s.x * w / 256 / 256)
        y = int(s.y * h / 256 / 256)
        if x >= w:
            x = x - w
        if x < 0:
            x = w + x
        if y >= h:
            y = y - h
        if y < 0:
            y = y + h
        c = s.color
        b = min(100, s.brightness)
        c = (int(c[0] * b / 100), int(c[1] * b / 100), int(c[2] * b / 100))
        return Projection(x=x, y=y, c = c, s = s.brightness)
    def draw(self, w, h, txt):
        img = Image.new('RGB', (w, h), color='black')
        px = img.load()
        cnv = ImageDraw.Draw(img)
        for s in self.stars.values():
            p = self.project(s, w, h)
            if p.s > 100:
                cnv.ellipse( (p.x - 1, p.y -1, p.x + 1, p.y + 1), p.c, None, 0)
            else:
                px[p.x, p.y] = p.c
        # ImageDraw.Draw(img).text((0, 0), txt + " " + str(len(self.stars)), (200, 200, 200))
        cnv.text((0, 0), txt + " " + str(len(self.stars)), (200, 200, 200))
        return img


def commented():
    img = Image.new('RGB', (1200, 800), color='black')
    px = img.load()
    cnt = 0
    skipped = 0
    max_scale = 0

    import sys
    for root, dirs, files in os.walk(sys.argv[1]):
        scale = len(files)
        max_scale = max(max_scale, scale)
        if scale < 1:
            continue
        mult = math.log(scale, 2)
        for name in files:
            dname = root
            fname = name
            print(name, ':', dname, fname)
            h = blake2b(digest_size=4)
            h.update(bytes(dname, 'utf-8'))
            d = h.digest()
            x = d[0]*256+d[1]
            y = d[2]*256+d[3]

            hn = blake2b(digest_size=2)
            hn.update(bytes(fname, 'utf-8'))
            dn = hn.digest()
            dist = dn[0] * dn[0] / 256 * mult * 3
            angle = dn[1]
            x = x + dist * math.cos(angle)
            y = y + dist * math.sin(angle)
            # x = x + (dn[0] - 128) * mult * 3
            # y = y + (dn[1] - 128) * mult * 3

            x = int(x * 1200 / 256 / 256)
            y = int(y * 800 / 256 / 256)
            if x >= 1200:
                x = x - 1200
            if x < 0:
                x = 1200 + x
            if y >= 800:
                y = y - 800
            if y < 0:
                y = y + 800
            # if x >= 1200 or x < 0:
            #     skipped += 1
            #     continue
            #
            # if y >= 800 or y < 0:
            #     skipped += 1
            #     continue

            color = (127, 127, 195)
            if "Test" in name:
                color = (127, 195, 195)
            if name.endswith('.cs'):
                color = (195, 127, 127)
            if name.endswith('.h'):
                color = (195, 195, 195)
            px[x, y] = color
            cnt += 1

    print(cnt, skipped)
    print(max_scale)
    # for i in range(800):
    #     px[i, i] = (127, 127, 127)
    img.save('stars.gif')

import sys
sky = Sky()
result = read_history(sys.argv[1])
for k in sorted(result.keys()):
    print(k, len(result[k]))
    for s in result[k]:
        dname = os.path.dirname(s)
        fname = os.path.basename(s)
        sky.update(dname, fname)
print(skipped_lines)
print(sky.scales)
images = []
for k in sorted(result.keys()):
    sky.advance(result[k])
    images.append(sky.draw(1200, 800, k))
    print(k, len(result[k]), sky.brightest, sky.max_brightness)

images[0].save('sky.gif', save_all=True, append_images=images[1:], optimize=False, loop=0, duration=100)
