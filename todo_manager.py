"""
Task Vault - A command-line to-do list manager
Persists tasks to disk as JSON, tracks priority/category/due dates,
and supports search, editing, and overdue detection.
"""

import json
from pathlib import Path
from datetime import date, datetime

DATA_FILE = Path("tasks.json")

PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}
PRIORITIES = ("High", "Medium", "Low")
CATEGORIES = ("Work", "Study", "Personal")


class Task:
    """A single to-do item. Knows how to serialize itself to/from a dict."""

    def __init__(self, task_id, title, priority, category, due_date,
                 done=False, created=None):
        self.task_id = task_id
        self.title = title
        self.priority = priority
        self.category = category
        self.due_date = due_date          # date object, or None
        self.done = done
        self.created = created or datetime.now().strftime("%Y-%m-%d %H:%M")

    @property
    def due_display(self):
        return self.due_date.isoformat() if self.due_date else "—"

    @property
    def status_label(self):
        return "DONE" if self.done else "open"

    def is_overdue(self, today=None):
        today = today or date.today()
        return (not self.done) and (self.due_date is not None) and self.due_date < today

    def is_due_on(self, target_day):
        return (not self.done) and self.due_date == target_day

    def matches_keyword(self, keyword):
        return keyword.lower() in self.title.lower()

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "title": self.title,
            "priority": self.priority,
            "category": self.category,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "done": self.done,
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, data):
        raw_due = data.get("due_date")
        due = date.fromisoformat(raw_due) if raw_due else None
        return cls(
            task_id=data["task_id"],
            title=data["title"],
            priority=data.get("priority", "Medium"),
            category=data.get("category", "Personal"),
            due_date=due,
            done=data.get("done", False),
            created=data.get("created"),
        )

    def as_row(self):
        return (str(self.task_id), self.title, self.priority,
                self.category, self.status_label, self.due_display)


class TaskVault:
    """Owns the collection of tasks and all disk I/O."""

    def __init__(self, path=DATA_FILE):
        self.path = path
        self.tasks = []
        self._load()

    # ---------- persistence ----------

    def _load(self):
        if not self.path.exists():
            self.tasks = []
            return
        with self.path.open("r") as fh:
            raw = json.load(fh)
        self.tasks = [Task.from_dict(item) for item in raw]

    def _persist(self):
        with self.path.open("w") as fh:
            json.dump([t.to_dict() for t in self.tasks], fh, indent=2)

    def _next_id(self):
        if not self.tasks:
            return 1
        return max(t.task_id for t in self.tasks) + 1

    # ---------- CRUD ----------

    def add(self, title, priority, category, due_date):
        task = Task(self._next_id(), title, priority, category, due_date)
        self.tasks.append(task)
        self._persist()
        return task

    def find(self, task_id):
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None

    def remove(self, task_id):
        task = self.find(task_id)
        if task is None:
            return None
        self.tasks.remove(task)
        self._persist()
        return task

    def complete(self, task_id):
        task = self.find(task_id)
        if task is None:
            return None, "missing"
        if task.done:
            return task, "already_done"
        task.done = True
        self._persist()
        return task, "done"

    def save(self):
        self._persist()

    # ---------- queries ----------

    def sorted_by_priority(self, pool=None):
        pool = self.tasks if pool is None else pool
        return sorted(pool, key=lambda t: PRIORITY_RANK.get(t.priority, 9))

    def pending(self):
        return [t for t in self.tasks if not t.done]

    def by_priority(self, level):
        return [t for t in self.tasks if t.priority == level]

    def search(self, keyword):
        return [t for t in self.tasks if t.matches_keyword(keyword)]

    def overdue(self, today=None):
        today = today or date.today()
        return [t for t in self.tasks if t.is_overdue(today)]

    def due_on(self, target_day):
        return [t for t in self.tasks if t.is_due_on(target_day)]

    def stats(self):
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t.done)
        pending = total - done
        high_open = sum(1 for t in self.tasks if t.priority == "High" and not t.done)
        overdue_count = len(self.overdue())
        pct = round((done / total) * 100) if total else 0
        return {
            "total": total,
            "done": done,
            "pending": pending,
            "high_open": high_open,
            "overdue": overdue_count,
            "pct": pct,
        }


# ---------------------------------------------------------------------------
# Console I/O helpers — kept separate from TaskVault so the model stays
# free of print()/input() calls.
# ---------------------------------------------------------------------------

def prompt_choice(label, options):
    """Ask the user to pick one of `options` (1-indexed) and return the value."""
    print(label)
    for i, opt in enumerate(options, start=1):
        print(f"  {i}) {opt}")
    while True:
        raw = input(f"Pick 1-{len(options)}: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("That's not a valid option, try again.")


def prompt_date(label="Due date (YYYY-MM-DD), or blank for none: "):
    while True:
        raw = input(label).strip()
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            print("Couldn't parse that date — use YYYY-MM-DD format.")


def print_table(tasks):
    if not tasks:
        print("(nothing here)")
        return
    header = ("ID", "Title", "Priority", "Category", "Status", "Due")
    widths = [4, 26, 9, 9, 7, 11]
    line = "  ".join(h.ljust(w) for h, w in zip(header, widths))
    print(line)
    print("-" * len(line))
    for t in tasks:
        row = t.as_row()
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


MENU_TEXT = """
========== TASK VAULT ==========
 1) Add a task
 2) List all tasks
 3) List open (pending) tasks
 4) List high-priority tasks
 5) Search by keyword
 6) List overdue tasks
 7) List tasks due today
 8) Edit a task
 9) Complete a task
10) Delete a task
11) Show stats
12) Quit
=================================
"""


def handle_add(vault):
    title = input("Title: ").strip()
    if not title:
        print("A task needs a title — nothing added.")
        return
    priority = prompt_choice("Priority?", list(PRIORITIES))
    category = prompt_choice("Category?", list(CATEGORIES))
    due = prompt_date()
    task = vault.add(title, priority, category, due)
    print(f"Added as task #{task.task_id}.")


def handle_list_all(vault):
    print_table(vault.sorted_by_priority())


def handle_list_pending(vault):
    print_table(vault.sorted_by_priority(vault.pending()))


def handle_list_high(vault):
    print_table(vault.sorted_by_priority(vault.by_priority("High")))


def handle_search(vault):
    keyword = input("Keyword: ").strip()
    if not keyword:
        print("Type something to search for.")
        return
    print_table(vault.search(keyword))


def handle_overdue(vault):
    print_table(vault.sorted_by_priority(vault.overdue()))


def handle_due_today(vault):
    print_table(vault.due_on(date.today()))


def _ask_task_id(prompt_label):
    raw = input(prompt_label).strip()
    if not raw.isdigit():
        print("IDs are numbers — try again next time.")
        return None
    return int(raw)


def handle_edit(vault):
    print_table(vault.sorted_by_priority())
    task_id = _ask_task_id("Task ID to edit: ")
    if task_id is None:
        return
    task = vault.find(task_id)
    if task is None:
        print(f"No task #{task_id}.")
        return

    field = prompt_choice(
        f"Editing '{task.title}' — what changes?",
        ["Title", "Priority", "Category", "Due date", "Nothing (cancel)"],
    )
    if field == "Title":
        new_title = input("New title: ").strip()
        if not new_title:
            print("Empty title rejected, task left as-is.")
            return
        task.title = new_title
    elif field == "Priority":
        task.priority = prompt_choice("New priority?", list(PRIORITIES))
    elif field == "Category":
        task.category = prompt_choice("New category?", list(CATEGORIES))
    elif field == "Due date":
        task.due_date = prompt_date()
    else:
        print("Cancelled — nothing changed.")
        return
    vault.save()
    print("Updated.")


def handle_complete(vault):
    print_table(vault.sorted_by_priority(vault.pending()))
    task_id = _ask_task_id("Task ID to mark complete: ")
    if task_id is None:
        return
    task, outcome = vault.complete(task_id)
    if outcome == "missing":
        print(f"No task #{task_id}.")
    elif outcome == "already_done":
        print(f"'{task.title}' was already done.")
    else:
        print(f"Nice — '{task.title}' marked complete.")


def handle_delete(vault):
    print_table(vault.sorted_by_priority())
    task_id = _ask_task_id("Task ID to delete: ")
    if task_id is None:
        return
    task = vault.find(task_id)
    if task is None:
        print(f"No task #{task_id}.")
        return
    confirm = input(f"Really delete '{task.title}'? (y/n): ").strip().lower()
    if confirm.startswith("y"):
        vault.remove(task_id)
        print("Deleted.")
    else:
        print("Left alone.")


def handle_stats(vault):
    s = vault.stats()
    print("\n----- STATS -----")
    print(f"Total tasks      : {s['total']}")
    print(f"Completed        : {s['done']}")
    print(f"Still open       : {s['pending']}")
    print(f"High-priority open: {s['high_open']}")
    print(f"Overdue          : {s['overdue']}")
    print(f"Completion rate  : {s['pct']}%")


ACTIONS = {
    "1": handle_add,
    "2": handle_list_all,
    "3": handle_list_pending,
    "4": handle_list_high,
    "5": handle_search,
    "6": handle_overdue,
    "7": handle_due_today,
    "8": handle_edit,
    "9": handle_complete,
    "10": handle_delete,
    "11": handle_stats,
}


def main():
    vault = TaskVault()
    print(f"Task Vault ready — {len(vault.tasks)} task(s) loaded from disk.")

    while True:
        print(MENU_TEXT)
        choice = input("Choose an option (1-12): ").strip()

        if choice == "12":
            print("See you later.")
            break

        action = ACTIONS.get(choice)
        if action is None:
            print("Not a valid option — pick a number from the menu.")
            continue
        action(vault)


if __name__ == "__main__":
    main()
