# Seed: 2 sites, 1 dept each, a Partner + Dept Head per site, cross-site employees.
# Run: bench --site siteops.localhost execute siteops.seed_structure.run
import frappe

def _user(email, first, last):
    if not frappe.db.exists("User", email):
        u = frappe.get_doc({"doctype": "User", "email": email, "first_name": first,
            "last_name": last, "send_welcome_email": 0, "new_password": "siteops123"})
        u.append("roles", {"role": "SiteOps User"})
        u.insert(ignore_permissions=True)
    else:
        u = frappe.get_doc("User", email)
        if not any(r.role == "SiteOps User" for r in u.roles):
            u.append("roles", {"role": "SiteOps User"}); u.save(ignore_permissions=True)
    return email

def _site(name):
    if not frappe.db.exists("SiteOps Site", name):
        frappe.get_doc({"doctype": "SiteOps Site", "site_name": name}).insert(ignore_permissions=True)
    return name

def _dept(name, site, head=None):
    existing = frappe.db.get_value("SiteOps Department", {"department_name": name, "site": site})
    if existing: return existing
    d = frappe.get_doc({"doctype": "SiteOps Department", "department_name": name,
        "site": site, "department_head": head}).insert(ignore_permissions=True)
    return d.name

def _assign(user, site, role, dept=None):
    if not frappe.db.exists("SiteOps Assignment", {"user": user, "site": site, "role": role}):
        frappe.get_doc({"doctype": "SiteOps Assignment", "user": user, "site": site,
            "role": role, "department": dept or None}).insert(ignore_permissions=True)

def run():
    # sites
    mum = _site("Mumbai"); ahm = _site("Ahmedabad")

    # users
    aarav = _user("aarav@opsconsole.com", "Aarav", "Shah")     # Partner Mumbai
    kabir = _user("kabir@opsconsole.com", "Kabir", "Mehta")    # Partner Ahmedabad
    priya = _user("priya@opsconsole.com", "Priya", "Desai")    # Dept Head Mumbai
    rahul = _user("rahul@opsconsole.com", "Rahul", "Nair")     # Dept Head Ahmedabad
    sana  = _user("sana@opsconsole.com",  "Sana",  "Kapoor")   # Employee BOTH
    vikram= _user("vikram@opsconsole.com","Vikram","Rao")      # Employee BOTH
    neha  = _user("neha@opsconsole.com",  "Neha",  "Patel")    # Employee Ahmedabad

    # departments (one per site), headed by the dept heads
    mum_sales = _dept("Sales", mum, priya)
    ahm_sales = _dept("Sales", ahm, rahul)

    # partners (one per site)
    _assign(aarav, mum, "Partner")
    _assign(kabir, ahm, "Partner")

    # dept heads (one per site)
    _assign(priya, mum, "Dept Head", mum_sales)
    _assign(rahul, ahm, "Dept Head", ahm_sales)

    # cross-site employees:
    # Sana works in BOTH sites
    _assign(sana, mum, "Employee", mum_sales)
    _assign(sana, ahm, "Employee", ahm_sales)
    # Vikram also works in BOTH sites
    _assign(vikram, mum, "Employee", mum_sales)
    _assign(vikram, ahm, "Employee", ahm_sales)
    # Neha only in Ahmedabad
    _assign(neha, ahm, "Employee", ahm_sales)

    frappe.db.commit()
    print("=== Structure seeded ===")
    print("Sites:", frappe.db.count("SiteOps Site"))
    print("Departments:", frappe.db.count("SiteOps Department"))
    print("Assignments:", frappe.db.count("SiteOps Assignment"))
    print("")
    print("Partners:  Aarav (Mumbai), Kabir (Ahmedabad)")
    print("DeptHeads: Priya (Mumbai/Sales), Rahul (Ahmedabad/Sales)")
    print("Employees: Sana (BOTH), Vikram (BOTH), Neha (Ahmedabad)")
    print("All passwords: siteops123")
