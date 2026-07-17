# Scheduled jobs for SiteOps.
# Place at: apps/siteops/siteops/tasks.py
# Wire in hooks.py (see README) and enable the scheduler.
import frappe
from frappe.utils import today, add_days, add_months, getdate


def send_pending_reminders():
    """Daily: email each user a list of their pending tasks (not Done),
    every day until the tasks are completed."""
    rows = frappe.get_all(
        "SiteOps Task",
        filters={"status": ["!=", "Done"], "assigned_to": ["is", "set"]},
        fields=["name", "title", "status", "priority", "site", "assigned_to"],
        order_by="priority desc",
    )
    by_user = {}
    for r in rows:
        by_user.setdefault(r.assigned_to, []).append(r)

    for user, tasks in by_user.items():
        if not frappe.db.exists("User", user):
            continue
        enabled = frappe.db.get_value("User", user, "enabled")
        if not enabled or user in ("Administrator", "Guest"):
            continue
        lines = "".join(
            f"<li><b>{frappe.utils.escape_html(t.title)}</b> — {t.status}"
            f"{' · ' + t.priority if t.priority else ''} · {t.site}</li>"
            for t in tasks
        )
        try:
            frappe.sendmail(
                recipients=[user],
                subject=f"You have {len(tasks)} pending task(s) — Site Ops",
                message=(
                    f"<p>Hello,</p>"
                    f"<p>These tasks are still pending and need your attention:</p>"
                    f"<ul>{lines}</ul>"
                    f"<p>You will receive this reminder daily until they are completed.</p>"
                ),
            )
        except Exception:
            frappe.log_error(frappe.get_traceback(), "SiteOps reminder failed")


def regenerate_recurring():
    """Daily: for tasks with a Repeat setting, create a fresh copy when due
    (every day / 7 days / month), and schedule the next one."""
    rows = frappe.get_all(
        "SiteOps Task",
        filters={"recurrence": ["in", ["Daily", "Weekly", "Monthly"]], "parent_task": ["is", "not set"]},
        fields=["name", "title", "site", "department", "assigned_to", "priority", "recurrence", "next_recur_date"],
    )
    tdy = getdate(today())
    for r in rows:
        # first run: schedule from today without creating a duplicate
        if not r.next_recur_date:
            frappe.db.set_value("SiteOps Task", r.name, "next_recur_date", _next(tdy, r.recurrence), update_modified=False)
            continue
        if getdate(r.next_recur_date) > tdy:
            continue
        # due: create a fresh copy (Open), keep same repeat settings on the new one
        new = frappe.get_doc({
            "doctype": "SiteOps Task",
            "title": r.title,
            "site": r.site,
            "department": r.department,
            "assigned_to": r.assigned_to,
            "priority": r.priority,
            "status": "Open",
            "recurrence": r.recurrence,
            "next_recur_date": _next(tdy, r.recurrence),
            "history": [{"activity_type": "create", "detail": f"auto-created ({r.recurrence.lower()} repeat)", "actor": "Administrator"}],
        })
        new.insert(ignore_permissions=True)
        # stop the old one from repeating again (the new copy carries the repeat)
        frappe.db.set_value("SiteOps Task", r.name, "recurrence", "None", update_modified=False)
        frappe.db.set_value("SiteOps Task", r.name, "next_recur_date", None, update_modified=False)
    frappe.db.commit()


def _next(from_date, recurrence):
    if recurrence == "Daily":
        return add_days(from_date, 1)
    if recurrence == "Weekly":
        return add_days(from_date, 7)
    return add_months(from_date, 1)
