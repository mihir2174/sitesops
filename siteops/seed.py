# Seed dummy data for the SiteOps app.
# Run with: bench --site siteops.localhost execute siteops.seed.run
# (after placing this file at apps/siteops/siteops/seed.py)
import frappe
from datetime import datetime, timedelta

def _days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d %H:%M:%S")

def run():
    # ---- Users (people) ----
    users = [
        ("ashok@opsconsole.com", "Ashok", "Mehta"),
        ("kiran@opsconsole.com", "Kiran", "Shah"),
        ("priya@opsconsole.com", "Priya", "Desai"),
        ("manish@opsconsole.com", "Manish", "Rana"),
        ("rakesh@opsconsole.com", "Rakesh", "Joshi"),
        ("neha@opsconsole.com", "Neha", "Patel"),
    ]
    for email, first, last in users:
        if not frappe.db.exists("User", email):
            u = frappe.get_doc({
                "doctype": "User", "email": email, "first_name": first, "last_name": last,
                "send_welcome_email": 0, "new_password": "siteops123",
                "roles": [{"role": "SiteOps User"}],
            })
            u.insert(ignore_permissions=True)
    frappe.db.commit()

    # ---- Sites ----
    sites = ["Mumbai", "Ahmedabad"]
    for s in sites:
        if not frappe.db.exists("SiteOps Site", s):
            frappe.get_doc({"doctype": "SiteOps Site", "site_name": s}).insert(ignore_permissions=True)
    frappe.db.commit()

    # ---- Departments ----
    depts = [
        ("Sales team", "Mumbai", "ashok@opsconsole.com"),
        ("Marketing team", "Mumbai", "priya@opsconsole.com"),
        ("Sales team", "Ahmedabad", "manish@opsconsole.com"),
    ]
    dept_names = {}
    for name, site, head in depts:
        existing = frappe.db.get_value("SiteOps Department", {"department_name": name, "site": site})
        if existing:
            dept_names[(name, site)] = existing
        else:
            d = frappe.get_doc({"doctype": "SiteOps Department", "department_name": name, "site": site, "department_head": head}).insert(ignore_permissions=True)
            dept_names[(name, site)] = d.name
    frappe.db.commit()

    # ---- Assignments (user, site, role, department) ----
    assigns = [
        ("ashok@opsconsole.com", "Mumbai", "Partner", None),
        ("kiran@opsconsole.com", "Ahmedabad", "Partner", None),
        ("priya@opsconsole.com", "Mumbai", "Dept Head", ("Marketing team", "Mumbai")),
        ("manish@opsconsole.com", "Mumbai", "Employee", ("Sales team", "Mumbai")),
        ("manish@opsconsole.com", "Ahmedabad", "Dept Head", ("Sales team", "Ahmedabad")),
        ("rakesh@opsconsole.com", "Mumbai", "Employee", ("Sales team", "Mumbai")),
        ("neha@opsconsole.com", "Ahmedabad", "Employee", ("Sales team", "Ahmedabad")),
    ]
    for user, site, role, deptkey in assigns:
        dept = dept_names.get(deptkey) if deptkey else None
        exists = frappe.db.exists("SiteOps Assignment", {"user": user, "site": site, "role": role})
        if not exists:
            frappe.get_doc({"doctype": "SiteOps Assignment", "user": user, "site": site, "role": role, "department": dept}).insert(ignore_permissions=True)
    frappe.db.commit()

    # ---- Tasks ----
    def mk_task(title, site, deptkey, assigned, status, notes=None, parent=None):
        dept = dept_names.get(deptkey) if deptkey else None
        doc = frappe.get_doc({
            "doctype": "SiteOps Task", "title": title, "site": site,
            "department": dept, "assigned_to": assigned, "status": status,
            "parent_task": parent,
            "notes": [{"note": n[0], "author": n[1]} for n in (notes or [])],
        })
        doc.insert(ignore_permissions=True)
        return doc.name

    # only seed tasks once (skip if any task exists)
    if not frappe.db.count("SiteOps Task"):
        t1 = mk_task("Close deal - Patel Textiles", "Mumbai", ("Sales team","Mumbai"), "rakesh@opsconsole.com", "In progress",
                     notes=[("Client wants revised pricing by Friday.", "ashok@opsconsole.com")])
        mk_task("Send revised quote", "Mumbai", ("Sales team","Mumbai"), "rakesh@opsconsole.com", "Open", parent=t1)
        mk_task("Q3 marketing creative review", "Mumbai", ("Marketing team","Mumbai"), "priya@opsconsole.com", "Open")
        mk_task("Follow up - Sharma Traders lead", "Mumbai", ("Sales team","Mumbai"), "manish@opsconsole.com", "Blocked")
        mk_task("Weekly leads report", "Mumbai", ("Sales team","Mumbai"), "manish@opsconsole.com", "Done")
        mk_task("Vendor onboarding - Ahmedabad", "Ahmedabad", ("Sales team","Ahmedabad"), "neha@opsconsole.com", "Open")
        mk_task("Ahmedabad pipeline sync", "Ahmedabad", ("Sales team","Ahmedabad"), "manish@opsconsole.com", "In progress")
    frappe.db.commit()

    print("=== Seed complete ===")
    print("Users:", frappe.db.count("User"))
    print("Sites:", frappe.db.count("SiteOps Site"))
    print("Departments:", frappe.db.count("SiteOps Department"))
    print("Assignments:", frappe.db.count("SiteOps Assignment"))
    print("Tasks:", frappe.db.count("SiteOps Task"))
