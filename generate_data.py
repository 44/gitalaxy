import subprocess
import os
from dataclasses import dataclass, field
from hashlib import blake2b
from functools import cache
import math
import json


class Galaxy:
    def __init__(self, path):
        if path.startswith("00"):
            raise f"Invalid path: {path}"
        self.size = 1
        self.path = path
        h = blake2b(digest_size=4)
        h.update(bytes(path, "utf-8"))
        d = h.digest()
        self.x = d[0] * 256 + d[1]
        self.y = d[2] * 256 + d[3]
        self.scale = 3 + d[0] % 3

    def add(self):
        self.size += 1


class Star:
    def __init__(self, g, fname):
        hn = blake2b(digest_size=2)
        hn.update(bytes(fname, "utf-8"))
        dn = hn.digest()
        dist = dn[0] * dn[0] / 256 * g.scale * 3
        angle = dn[1]
        self.x = int(g.x + dist * math.cos(angle))
        self.y = int(g.y + dist * math.sin(angle))
        self.fname = fname
        self.c = os.path.splitext(fname)[1][1:].lower()
        self.g = g
        fullpath = os.path.join(g.path, fname).lower()
        if "test" in fullpath:
            self.c = "test"

    def as_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "n": self.fname,
            "c": self.c,
            "g": self.g.path,
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
            "counter": self.counter,
        }


class Sky:
    def __init__(self, cfg):
        self.root = cfg.root
        self.galaxies = {}
        self.output = cfg.output
        self.exclude = cfg.exclude
        self.all_branches = cfg.all
        self.ignore = cfg.ignore
        self.changes = []
        self.saved = SavedState()

    def get_repo_name(self):
        git_args = ["git", "remote", "get-url", "origin"]
        c = subprocess.run(git_args, cwd=self.root, capture_output=True, text=True)
        if c.returncode != 0:
            return os.path.basename(self.root)
        name = os.path.basename(c.stdout.strip())
        if name.endswith(".git"):
            name = name[:-4]
        return name

    def load_galaxies(self):
        git_args = ["git", "ls-files"]
        c = subprocess.run(git_args, cwd=self.root, capture_output=True, text=True)
        if c.returncode != 0:
            raise f"Failed to load galaxies({c.returncode}): {c.stderr}"
        lines = c.stdout.split("\n")
        for line in lines:
            line = line.strip()
            if len(line) == 0:
                continue
            dname, fname = os.path.split(line)
            if dname not in self.galaxies:
                self.galaxies[dname] = Galaxy(dname)
            else:
                self.galaxies[dname].add()

    @cache
    def get_galaxy(self, dname):
        if dname not in self.galaxies:
            self.galaxies[dname] = Galaxy(dname)
        return self.galaxies[dname]

    @cache
    def get_star(self, dname, fname):
        return Star(self.get_galaxy(dname), fname)

    def save_changes(self, force=False):
        if self.saved.start is None:
            if len(self.changes) > 0:
                self.saved.start = self.changes[0]["date"]
        need_save = force
        if not need_save:
            size = 0
            for c in self.changes:
                size += len(c["on"]) + len(c["off"])
            if size < 10000:
                return

        if len(self.changes) == 0:
            return
        os.makedirs(self.output, exist_ok=True)
        json.dump(
            self.changes,
            open(f"{self.output}/{self.saved.counter}.json", "w"),
            indent=4,
        )
        if len(self.changes) > 0:
            self.saved.end = self.changes[-1]["date"]
            self.saved.commit = self.changes[-1]["commit"]
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
            self.saved.start = index["start"]
            self.saved.end = index["end"]
            self.saved.commit = index["commit"]
            self.saved.counter = index["counter"]
            self.saved.data = index["data"]

    def applicable_change(self, change):
        if change.author is None:
            return False
        if self.exclude is None:
            return True
        if change.author in self.exclude:
            return False
        return True

    def generate_changes(self):
        self.load_index()
        git_args = [
            "git",
            "log",
            "--format==%ad %H %ae",
            "--date=format:%Y-%m-%d",
            "--name-status",
            "--reverse",
            "--no-renames",
        ]
        if self.all_branches:
            git_args.append("--all")
        if self.saved.commit is not None:
            git_args.append(f"{self.saved.commit}..HEAD")
        c = subprocess.run(git_args, cwd=self.root, capture_output=True, text=True)
        if c.returncode != 0:
            raise f"Failed to load changes({c.returncode}): {c.stderr}"

        cnt = 0

        lines = c.stdout.split("\n")
        print(f"Loaded {len(lines)} lines")

        s = State()

        for line in lines:
            line = line.strip()
            if len(line) == 0:
                continue
            if line.startswith("="):
                if len(s.changed) > 0 or len(s.removed) > 0:
                    if self.applicable_change(s):
                        self.changes.append(
                            {
                                "id": cnt,
                                "date": s.date,
                                "commit": s.commit,
                                "author": s.author,
                                "on": s.changed,
                                "off": s.removed,
                            }
                        )
                    self.save_changes()
                    cnt += 1

                s = State()
                # format =2021-08-31 <commit - 40 chars> <author>
                s.date = line[1:11]
                s.commit = line[12:52]
                s.author = line[53:].strip()
                if "@" in s.author:
                    s.author = s.author.split("@")[0]
            else:
                fpath = line[2:].strip()
                ignored = False
                if self.ignore is not None:
                    for i in self.ignore:
                        if i in fpath:
                            ignored = True
                            break
                if ignored:
                    continue
                dname, fname = os.path.split(fpath)
                if line.startswith("D"):
                    s.removed.append(self.get_star(dname, fname).as_dict())
                elif line.startswith("R"):
                    pass
                else:
                    s.changed.append(self.get_star(dname, fname).as_dict())

        if self.applicable_change(s):
            self.changes.append(
                {
                    "id": cnt,
                    "date": s.date,
                    "commit": s.commit,
                    "author": s.author,
                    "on": s.changed,
                    "off": s.removed,
                }
            )
        self.save_changes(force=True)
        self.save_index()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r", "--root", help="root directory of the repository", required=True
    )
    parser.add_argument("-o", "--output", help="output directory", required=True)
    parser.add_argument("-x", "--exclude", help="exclude author", action="append")
    parser.add_argument("-a", "--all", help="include all branches", action="store_true")
    parser.add_argument("-i", "--ignore", help="ignore path", action="append")
    args = parser.parse_args()
    sky = Sky(args)
    sky.generate_changes()
