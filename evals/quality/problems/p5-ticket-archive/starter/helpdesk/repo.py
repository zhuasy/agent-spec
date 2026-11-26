"""Ticket storage: a JSON file holding a list of tickets.

A ticket is a dict:
    id          int
    title       str
    status      "open" or "closed"
    created_at  ISO time, e.g. "2026-01-05T09:30:00Z"
    closed_at   ISO time of the most recent close, or null
    legal_hold  bool, optional (missing means false)
"""
import json
import os
from datetime import datetime, timezone


def parse_time(text):
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def format_time(moment):
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TicketRepo:
    def __init__(self, path):
        self.path = path
        with open(path, encoding="utf-8") as f:
            self.tickets = json.load(f)

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.tickets, f, indent=2)
        os.replace(tmp, self.path)

    def get(self, ticket_id):
        for ticket in self.tickets:
            if ticket["id"] == ticket_id:
                return ticket
        raise KeyError(ticket_id)

    def search(self, status=None, text=None):
        found = []
        for ticket in self.tickets:
            if status is not None and ticket["status"] != status:
                continue
            if text is not None and text.lower() not in ticket["title"].lower():
                continue
            found.append(ticket)
        return found

    def close(self, ticket_id, now):
        ticket = self.get(ticket_id)
        ticket["status"] = "closed"
        ticket["closed_at"] = format_time(now)

    def reopen(self, ticket_id):
        ticket = self.get(ticket_id)
        ticket["status"] = "open"
