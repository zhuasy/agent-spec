"""Task storage: one JSON file."""
# reference implementation - EVAL-CANARY-7f3a9c1e-quality - never show to a role
import json
import os
import re

_TAG_RE = re.compile(r"^[a-z0-9-]+$")


def normalize_tag(tag):
    tag = tag.lower()
    if not _TAG_RE.match(tag):
        raise ValueError("invalid tag %r: use letters, digits and dashes" % tag)
    return tag


class Store:
    def __init__(self, path):
        self.path = path

    def _load(self):
        if not os.path.exists(self.path):
            return {"next_id": 1, "tasks": []}
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self.path)

    def add(self, title, tags=()):
        title = title.strip()
        if not title:
            raise ValueError("title must not be empty")
        tags = sorted({normalize_tag(t) for t in tags})
        data = self._load()
        task = {"id": data["next_id"], "title": title, "done": False, "tags": tags}
        data["tasks"].append(task)
        data["next_id"] += 1
        self._save(data)
        return task["id"]

    def done(self, task_id):
        data = self._load()
        for task in data["tasks"]:
            if task["id"] == task_id:
                task["done"] = True
                self._save(data)
                return
        raise KeyError(task_id)

    def list(self, include_done=False, tags=()):
        wanted = {normalize_tag(t) for t in tags}
        tasks = self._load()["tasks"]
        if not include_done:
            tasks = [t for t in tasks if not t["done"]]
        return [t for t in tasks if wanted <= set(t.get("tags", []))]

    def tag_counts(self):
        counts = {}
        for task in self.list():
            for tag in task.get("tags", []):
                counts[tag] = counts.get(tag, 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
