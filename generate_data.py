import subprocess
import sys
import os
from collections import defaultdict
from dataclasses import dataclass
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
    def add(self):
        self.size += 1
        self.scale = math.log(self.size, 4) + 1

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

class Sky:
    def __init__(self, root):
        self.root = root
        self.galaxies = {}
        self.changes = []

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

    def load_changes(self):
        # todo: load changes from files
        git_args = ['git', 'log', '--format==%ad %H %ae', '--date=format:%Y-%m-%d', '--name-status', '--reverse']
        c = subprocess.run(git_args, cwd=self.root, capture_output=True, text=True)
        if c.returncode != 0:
            raise f"Failed to load changes({c.returncode}): {c.stderr}"

        cnt = 0

        lines = c.stdout.split('\n')
        print(f"Loaded {len(lines)} lines")

        class State:
            id = 0
            date = None
            commit = None
            author = None
            changed = []
            removed = []
        s = State()

        current = None
        changed_files = []
        removed_files = []
        biggest = 0

        for l in lines:
            l = l.strip()
            if len(l) == 0:
                continue
            if l.startswith('='):
                if len(changed_files) > 0 or len(removed_files) > 0:
                    if current[2] is not None:
                        # print(f"Adding {current[1]} by {current[2]}")
                        self.changes.append({
                            "id": cnt,
                            "date": current[0],
                            "commit": current[1],
                            "author": current[2],
                            "flash": changed_files,
                            "gone": removed_files
                            })
                    size = len(changed_files) + len(removed_files)
                    if size > biggest:
                        biggest = size
                        print(f"New biggest: {biggest} by {current[2]} at {current[0]}")
                    removed_files = []
                    changed_files = []
                    cnt += 1

                d = l[1:11]
                cid = l[12:52]
                author = l[53:].strip()
                if "@" in author:
                    author = author.split("@")[0]
                    current = (d, cid, author)
                else:
                    current = (d, cid, None)
            else:
                fpath = l[2:].strip()
                dname, fname = os.path.split(fpath)
                if l.startswith('D'):
                    removed_files.append(self.get_star(dname, fname).as_dict())
                else:
                    changed_files.append(self.get_star(dname, fname).as_dict())

        if current[2] is not None:
            # print(f"Adding {current[1]} by {current[2]}")
            self.changes.append({
                "id": cnt,
                "date": current[0],
                "commit": current[1],
                "author": current[2],
                "flash": changed_files,
                "gone": removed_files
                })
        json.dump(self.changes, open("changes.json", "w"), indent=4)

def get_history(root):
    git_args = ['git', 'log', '--format==%ad %H %ae', '--date=format:%Y-%m-%d', '--name-status', '--reverse']
    c = subprocess.run(git_args, cwd=sys.argv[1], capture_output=True, text=True)

    changes = []
    cnt = 0

    lines = c.stdout.split('\n')
    current = None
    changed_files = []
    removed_files = []
    biggest = 0

    for l in lines:
        l = l.strip()
        if len(l) == 0:
            continue
        print(l)
        if l.startswith('='):
            if len(changed_files) > 0 or len(removed_files) > 0:
                if current[2] is not None:
                    changes.append({"id": cnt, "date": current[0], "commit": current[1], "author": current[2], "touched": changed_files, "gone": removed_files})
                size = len(changed_files) + len(removed_files)
                if size > biggest:
                    biggest = size
                    print(f"New biggest: {biggest} by {current[2]} at {current[0]}")
                removed_files = []
                changed_files = []
                cnt += 1

            d = l[1:11]
            cid = l[12:52]
            author = l[53:].strip()
            if "@" in author:
                author = author.split("@")[0]
                current = (d, cid, author)
            else:
                current = (d, cid, None)
        else:
            if l.startswith('D'):
                removed_files.append(l[2:].strip())
            else:
                changed_files.append(l[2:].strip())
    import json
    ordered = sorted(changes, key=lambda x: x['id'], reverse=True)

    file_cnt = 0
    last_cutoff = 0
    current_number = 0

    for i in range(len(ordered)):
        current_number += len(ordered[i]['touched']) + len(ordered[i]['gone'])
        if current_number > 10000:
            print(f"Saved {file_cnt}: {last_cutoff} - {i}")
            json.dump(ordered[last_cutoff:i+1], open(f"changes_{file_cnt}.json", "w"), indent=4)
            last_cutoff = i
            current_number = 0
            file_cnt += 1

    print(f"Saved {file_cnt}: {last_cutoff} - {len(ordered)}")
    json.dump(ordered[last_cutoff:], open(f"changes_{file_cnt}.json", "w"), indent=4)

if __name__ == "__main__":
    sky = Sky(sys.argv[1])
    sky.load_galaxies()
    import math
    for d, s in sorted(sky.galaxies.items(), key=lambda x: x[1].size, reverse=False):
        print(d, s.size, int(math.log(s.size, 4) + 1), s.x, s.y)
    sky.load_changes()
