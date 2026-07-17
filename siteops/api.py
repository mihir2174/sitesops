# Server-side API for the SiteOps app.
# Place at: apps/siteops/siteops/api.py
import frappe
from frappe import _


# ---------- helpers ----------
def _sites_i_manage():
    """Sites the current user may manage users for.
    Super Admin (System Manager or Administrator) -> all sites (None = unrestricted).
    Partner -> the sites where they have a Partner assignment."""
    u = frappe.session.user
    if u == "Administrator" or "System Manager" in frappe.get_roles(u):
        return None  # unrestricted
    partner_sites = frappe.get_all("SiteOps Assignment",
        filters={"user": u, "role": "Partner"}, pluck="site")
    return list(set(partner_sites))


def _assert_can_manage_site(site):
    allowed = _sites_i_manage()
    if allowed is None:
        return
    if site not in allowed:
        frappe.throw(_("You can only manage users in your own site."), frappe.PermissionError)


def _assert_can_manage_user(email):
    """A manager may manage a user if that user has at least one assignment
    in a site the manager controls."""
    allowed = _sites_i_manage()
    if allowed is None:
        return
    user_sites = frappe.get_all("SiteOps Assignment", filters={"user": email}, pluck="site")
    if not any(s in allowed for s in user_sites):
        frappe.throw(_("This user is not in a site you manage."), frappe.PermissionError)


# ---------- read ----------
@frappe.whitelist()
def list_managed_users():
    """Return users the current manager can see, with their assignments."""
    allowed = _sites_i_manage()
    if allowed is None:
        emails = frappe.get_all("User",
            filters={"name": ["not in", ["Administrator", "Guest"]], "enabled": 1},
            pluck="name")
    else:
        rows = frappe.get_all("SiteOps Assignment", filters={"site": ["in", allowed]}, pluck="user")
        emails = list(set(rows))
    out = []
    for e in emails:
        if not frappe.db.exists("User", e):
            continue
        ud = frappe.db.get_value("User", e, ["name", "full_name", "email", "enabled"], as_dict=True)
        assigns = frappe.get_all("SiteOps Assignment", filters={"user": e},
            fields=["name", "site", "role", "department"])
        out.append({"user": ud.name, "full_name": ud.full_name, "email": ud.email, "enabled": ud.enabled, "assignments": assigns})
    return out


# ---------- create ----------
@frappe.whitelist()
def create_person(full_name, email, site, role, department=None, password=None, send_welcome_email=0):
    """Create (or reuse) a User, ensure SiteOps User role, set password if given,
    and create a SiteOps Assignment linking them to a site/role/department."""
    if not full_name or not email or not site or not role:
        frappe.throw(_("full_name, email, site and role are required"))
    _assert_can_manage_site(site)
    email = email.strip().lower()

    if not frappe.db.exists("User", email):
        parts = full_name.strip().split(" ", 1)
        user = frappe.get_doc({
            "doctype": "User", "email": email,
            "first_name": parts[0], "last_name": parts[1] if len(parts) > 1 else "",
            "send_welcome_email": 1 if int(send_welcome_email or 0) else 0,
        })
        user.append("roles", {"role": "SiteOps User"})
        if password:
            user.new_password = password
        user.insert(ignore_permissions=True)
    else:
        user = frappe.get_doc("User", email)
        if not any(r.role == "SiteOps User" for r in user.roles):
            user.append("roles", {"role": "SiteOps User"})
        if password:
            user.new_password = password
        user.save(ignore_permissions=True)

    if not frappe.db.exists("SiteOps Assignment", {"user": email, "site": site, "role": role}):
        frappe.get_doc({"doctype": "SiteOps Assignment", "user": email, "site": site,
            "role": role, "department": department or None}).insert(ignore_permissions=True)

    frappe.db.commit()
    return {"user": email}


# ---------- edit ----------
@frappe.whitelist()
def update_person(email, full_name=None, enabled=None):
    _assert_can_manage_user(email)
    user = frappe.get_doc("User", email)
    if full_name:
        parts = full_name.strip().split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""
    if enabled is not None:
        user.enabled = 1 if int(enabled) else 0
    user.save(ignore_permissions=True)
    frappe.db.commit()
    return {"user": email}


# ---------- password ----------
@frappe.whitelist()
def set_password(email, password):
    if not password or len(password) < 4:
        frappe.throw(_("Password must be at least 4 characters"))
    _assert_can_manage_user(email)
    from frappe.utils.password import update_password
    update_password(email, password)
    frappe.db.commit()
    return {"user": email, "ok": True}


# ---------- delete ----------
@frappe.whitelist()
def delete_person(email):
    _assert_can_manage_user(email)
    if email in ("Administrator", "Guest"):
        frappe.throw(_("This user cannot be deleted."))
    # remove their assignments first, then the user
    for a in frappe.get_all("SiteOps Assignment", filters={"user": email}, pluck="name"):
        frappe.delete_doc("SiteOps Assignment", a, force=True, ignore_permissions=True)
    frappe.delete_doc("User", email, force=True, ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True}
