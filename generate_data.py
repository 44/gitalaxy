import subprocess
import sys
import os
from collections import defaultdict
from dataclasses import dataclass, field
from hashlib import blake2b
from functools import cache
import math
import json

class Galaxy:
    def __init__(self, path):
        self.size = 1
        self.path = path
        h = blake2b(digest_size=4)
        h.update(bytes(path, 'utf-8'))
        d = h.digest()
        self.x = d[0]*256+d[1]
        self.y = d[2]*256+d[3]
        self.scale = 1
        self.scale = 3 + d[0] % 3
    def add(self):
        self.size += 1
        # self.scale = math.log(self.size, 4) + 1

class Star:
    def __init__(self, g, fname):
        hn = blake2b(digest_size=2)
        hn.update(bytes(fname, 'utf-8'))
        dn = hn.digest()
        dist = dn[0] * dn[0] / 256 * g.scale * 3
        angle = dn[1]
        self.x = int(g.x + dist * math.cos(angle))
        self.y = int(g.y + dist * math.sin(angle))
        self.fname = fname
        self.c = os.path.splitext(fname)[1][1:].lower()
        fullpath = os.path.join(g.path, fname).lower()
        if "test" in fullpath:
            self.c = "test"
    def as_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "fname": self.fname,
            "c": self.c
        }

@dataclass
class State:
    date: str = None
    commit: str = None
    author: str = None
    changed: list[dict] = field(default_factory=list)
    removed: list[dict] = field(default_factory=list)

@dataclass
class SavedState:
    start: str = None
    end: str = None
    data: list[str] = field(default_factory=list)
    commit: str = None
    counter: int = 0
    def as_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "data": self.data,
            "commit": self.commit,
            "counter": self.counter
        }

class Sky:
    def __init__(self, root, output, exclude):
        self.root = root
        self.galaxies = {}
        self.output = output
        self.exclude = exclude
        self.changes = []
        self.saved = SavedState()

    def get_repo_name(self):
        git_args = ['git', 'remote', 'get-url', 'origin']
        c = subprocess.run(git_args, cwd=self.root, capture_output=True, text=True)
        if c.returncode != 0:
            return os.path.basename(self.root)
        name = os.path.basename(c.stdout.strip())
        if name.endswith(".git"):
            name = name[:-4]
        return name

    def load_galaxies(self):
        git_args = ['git', 'ls-files']
        c = subprocess.run(git_args, cwd=self.root, capture_output=True, text=True)
        if c.returncode != 0:
            raise f"Failed to load galaxies({c.returncode}): {c.stderr}"
        lines = c.stdout.split('\n')
        for l in lines:
            l = l.strip()
            if len(l) == 0:
                continue
            dname, fname = os.path.split(l)
            if not dname in self.galaxies:
                self.galaxies[dname] = Galaxy(dname)
            else:
                self.galaxies[dname].add()

    @cache
    def get_galaxy(self, dname):
        if not dname in self.galaxies:
            self.galaxies[dname] = Galaxy(dname)
        return self.galaxies[dname]

    @cache
    def get_star(self, dname, fname):
        return Star(self.get_galaxy(dname), fname)

    def save_changes(self, force=False):
        if self.saved.start is None:
            if len(self.changes) > 0:
                self.saved.start = self.changes[0]['date']
        need_save = force
        if not need_save:
            size = 0
            for c in self.changes:
                size += len(c['on']) + len(c['off'])
            if size < 10000:
                return

        if len(self.changes) == 0:
            return
        os.makedirs(self.output, exist_ok=True)
        json.dump(self.changes, open(f"{self.output}/{self.saved.counter}.json", "w"), indent=4)
        if len(self.changes) > 0:
            self.saved.end = self.changes[-1]['date']
            self.saved.commit = self.changes[-1]['commit']
        self.changes = []
        self.saved.data.append(f"{self.saved.counter}.json")
        print(f"Saved {self.saved.counter} changes")
        self.saved.counter += 1

    def save_index(self):
        idx = self.saved.as_dict()
        idx["name"] = self.get_repo_name()
        json.dump(idx, open(f"{self.output}/index.json", "w"), indent=4)

    def load_index(self):
        if os.path.exists(f"{self.output}/index.json"):
            index = json.load(open(f"{self.output}/index.json", "r"))
            self.saved.start = index['start']
            self.saved.end = index['end']
            self.saved.commit = index['commit']
            self.saved.counter = index['counter']
            self.saved.data = index['data']

    def applicable_change(self, change):
        if change.author is None:
            return False
        if change.author in self.exclude:
            return False
        return True

    def generate_changes(self):
        self.load_index()
        git_args = ['git', 'log', '--format==%ad %H %ae', '--date=format:%Y-%m-%d', '--name-status', '--reverse']
        if self.saved.commit is not None:
            git_args.append(f"{self.saved.commit}..HEAD")
        c = subprocess.run(git_args, cwd=self.root, capture_output=True, text=True)
        if c.returncode != 0:
            raise f"Failed to load changes({c.returncode}): {c.stderr}"

        cnt = 0

        lines = c.stdout.split('\n')
        print(f"Loaded {len(lines)} lines")

        s = State()

        current = None
        biggest = 0

        for l in lines:
            l = l.strip()
            if len(l) == 0:
                continue
            if l.startswith('='):
                if len(s.changed) > 0 or len(s.removed) > 0:
                    if self.applicable_change(s):
                        self.changes.append({
                            "id": cnt,
                            "date": s.date,
                            "commit": s.commit,
                            "author": s.author,
                            "on": s.changed,
                            "off": s.removed
                            })
                    self.save_changes()
                    cnt += 1

                s = State()
                # format =2021-08-31 <commit - 40 chars> <author>
                s.date = l[1:11]
                s.commit = l[12:52]
                s.author = l[53:].strip()
                if "@" in s.author:
                    s.author = s.author.split("@")[0]
            else:
                fpath = l[2:].strip()
                dname, fname = os.path.split(fpath)
                if l.startswith('D'):
                    s.removed.append(self.get_star(dname, fname).as_dict())
                else:
                    s.changed.append(self.get_star(dname, fname).as_dict())

        if self.applicable_change(s):
            self.changes.append({
                "id": cnt,
                "date": s.date,
                "commit": s.commit,
                "author": s.author,
                "on": s.changed,
                "off": s.removed
                })
        self.save_changes(force=True)
        self.save_index()

def collapse(sky):
    new_galaxies = dict()

    for d, s in sky.galaxies.items():
        new_galaxies[d] = s.size

    while True:
        try:
            ordered = sorted(new_galaxies.items(), key=lambda e: len(e[0].split("/")), reverse=True)
            d, s = next(x for x in ordered if x[1] < 100 and len(x[0]) > 0)
            parent = os.path.dirname(d)
            if parent in new_galaxies:
                new_galaxies[parent] += s
            else:
                new_galaxies[parent] = s
            del new_galaxies[d]
        except:
            break
    return new_galaxies

def update_galaxies(sky, new_galaxies):
    for d, s in new_galaxies.items():
        if not d in sky.galaxies:
            sky.galaxies[d] = Galaxy(d)
        sky.galaxies[d].size = s
        sky.galaxies[d].scale = math.log(s, 4) + 1

    relink = []

    for d, s in sky.galaxies.items():
        if d in new_galaxies:
            continue
        parent = os.path.dirname(d)
        while True:
            if parent in new_galaxies:
                relink.append( (d, parent) )
                break
            parent = os.path.dirname(parent)

    for d, parent in relink:
        sky.galaxies[d] = sky.galaxies[parent]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--root', help='root directory of the repository', required=True)
    parser.add_argument('-o', '--output', help='output directory', required=True)
    parser.add_argument('-x', '--exclude', help='exclude author', action='append')
    args = parser.parse_args()
    sky = Sky(args.root, args.output, args.exclude)
    # sky.load_galaxies()
    # import math
    # for d, s in sorted(sky.galaxies.items(), key=lambda x: x[1].size, reverse=False):
    #     print(d, s.size, int(math.log(s.size, 4) + 1), s.x, s.y)
    # update_galaxies(sky, collapse(sky))
    sky.generate_changes()
