# Task Vault — To-Do List Manager

CloudExify Python Internship — Month 2, Project 4 (Final Project)
**Your Name:** Basit Ali
**Registration Number:**CX-INT-2026-PY_0160

An original, class-based implementation (not copied from the course handout):
a `Task` class models one item, a `TaskVault` class owns the collection and
all file I/O, and thin `handle_*()` functions do the console input/output.
Due dates are stored and compared as real `date` objects instead of strings.

## Features
- Add tasks with title, priority (High/Medium/Low), category (Work/Study/Personal), due date
- List all tasks (sorted High → Low priority)
- List only open (pending) tasks
- List only High-priority tasks
- **Search** tasks by keyword in the title
- **List overdue tasks** — open tasks whose due date has passed
- **List tasks due today**
- **Edit** any task's title, priority, category, or due date
- Mark a task complete
- Delete a task (with y/n confirmation)
- Stats: total, completed, open, high-priority-open, overdue, completion %
- Everything auto-saves to `tasks.json` after every change
- IDs never reuse a deleted number — always `max existing ID + 1`

## How to Run
```bash
python3 todo_manager.py
```
Pick a number 1–12 from the menu each time it's shown.

## Files
- `todo_manager.py` — the program
- `tasks.json` — created automatically the first time you add a task

## Design Notes
- `Task.from_dict` / `Task.to_dict` handle JSON serialization, including
  converting the due date to/from ISO date strings.
- Invalid menu picks, non-numeric IDs, malformed dates, and empty titles
  are all caught and re-prompted or rejected with a clear message —
  the program never crashes on bad input.
- `TaskVault.stats()` computes overdue count using the same `is_overdue()`
  logic as the "List overdue tasks" menu option, so the numbers always agree.
