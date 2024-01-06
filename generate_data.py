from git import Repo
import sys
from collections import defaultdict

authors=defaultdict(int)

repo = Repo(sys.argv[1])

current = set()

try:
    current.add(repo.heads.main.commit)
except:
    pass

try:
    current.add(repo.heads.master.commit)
except:
    pass

if len(current) == 0:
    print("Could not find neither main nor master branch")
    sys.exit(1)

while True:
    if len(current) == 0:
        break
    earliest = sorted(current, key=lambda x: x.authored_datetime, reverse = True)[0]
    current.discard(earliest)

    # print("SHA", current.hexsha)
    # print("Summary", current.summary)
    print("Commit", earliest.authored_datetime, earliest.author.email, earliest.hexsha)
    # print("Author", current.author.name)
    # print("Author email", current.author.email)
    # print("Files", current.stats.files)
    authors[f"{earliest.author.email} {earliest.author.name}"] += 1
    print("Files", earliest.stats.files)

    parents = earliest.parents
    for p in parents:
        current.add(p)

for author in sorted(authors.keys()):
    print(author, authors[author])
