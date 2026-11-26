"""Task storage: one JSON file."""
import json
import os


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

    def add(self, title):
        title = title.strip()
        if not title:
            raise ValueError("title must not be empty")
        data = self._load()
        task = {"id": data["next_id"], "title": title, "done": False}
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

    def list(self, include_done=False):
        tasks = self._load()["tasks"]
        if not include_done:
            tasks = [t for t in tasks if not t["done"]]
        return tasks
