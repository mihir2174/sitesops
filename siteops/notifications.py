# In-app + email notifications for SiteOps task assignment and status changes.
# Place at: apps/siteops/siteops/notifications.py
# Wire in hooks.py doc_events (see README).
import frappe


def on_task_update(doc, method=None):
    """Fires after a SiteOps Task is updated. Detects assignment and status
    changes by comparing with the previous version, and notifies the relevant
    user via a Notification Log entry (Frappe bell icon) + email if configured."""
    before = doc.get_doc_before_save()
    if not before:
        return

    if doc.assigned_to and doc.assigned_to != before.assigned_to:
        _notify(
            user=doc.assigned_to,
            subject=f"New task assigned: {doc.title}",
            message=f"You have been assigned the task '{doc.title}' ({doc.site}).",
            doc=doc,
        )

    if doc.status != before.status and doc.assigned_to:
        actor = frappe.session.user
        if actor != doc.assigned_to:
            _notify(
                user=doc.assigned_to,
                subject=f"Task status updated: {doc.title}",
                message=f"'{doc.title}' status changed from {before.status} to {doc.status}.",
                doc=doc,
            )


def on_task_insert(doc, method=None):
    """Fires when a new task is created with an assignee."""
    if doc.assigned_to and doc.assigned_to != frappe.session.user:
        _notify(
            user=doc.assigned_to,
            subject=f"New task assigned: {doc.title}",
            message=f"You have been assigned the task '{doc.title}' ({doc.site}).",
            doc=doc,
        )


def _notify(user, subject, message, doc):
    if not frappe.db.exists("User", user) or user in ("Administrator", "Guest"):
        return
    try:
        frappe.get_doc({
            "doctype": "Notification Log",
            "for_user": user,
            "subject": subject,
            "email_content": message,
            "document_type": "SiteOps Task",
            "document_name": doc.name,
            "type": "Alert",
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "SiteOps notify (in-app) failed")
    try:
        frappe.sendmail(recipients=[user], subject=subject, message=f"<p>{message}</p>")
    except Exception:
        pass
