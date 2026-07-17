# Seed sample tasks: all statuses + transferred ones (with history).
# Run AFTER seed_structure. Command:
#   bench --site siteops.localhost execute siteops.seed_tasks.run
import frappe

def _dept(name, site):
    return frappe.db.get_value("SiteOps Department", {"department_name": name, "site": site})

def _mktask(title, site, dept, assigned, status, history=None, notes=None):
    doc = frappe.get_doc({
        "doctype": "SiteOps Task",
        "title": title, "site": site, "department": dept,
        "assigned_to": assigned, "status": status,
        "notes": [{"note": n[0], "author": n[1]} for n in (notes or [])],
        "history": [{"activity_type": h[0], "detail": h[1], "actor": h[2]} for h in (history or [])],
    })
    doc.insert(ignore_permissions=True)
    return doc.name

def run():
    mum, ahm = "Mumbai", "Ahmedabad"
    mum_sales = _dept("Sales", mum); ahm_sales = _dept("Sales", ahm)

    aarav="aarav@opsconsole.com"; kabir="kabir@opsconsole.com"
    priya="priya@opsconsole.com"; rahul="rahul@opsconsole.com"
    sana="sana@opsconsole.com"; vikram="vikram@opsconsole.com"; neha="neha@opsconsole.com"

    if frappe.db.count("SiteOps Task"):
        print("Tasks already exist — skipping to stay idempotent. (Clear tasks first to re-seed.)")
        return

    # ---- Mumbai ----
    # Open
    _mktask("Prepare Q3 sales pitch — Mumbai", mum, mum_sales, sana, "Open",
        history=[("create", "created this task and assigned it to Sana Kapoor", priya)])
    # In progress
    _mktask("Follow up with Patel Textiles", mum, mum_sales, vikram, "In progress",
        history=[("create", "created this task and assigned it to Vikram Rao", aarav),
                 ("status", "changed status to In progress", vikram)],
        notes=[("Client asked for a revised quote by Friday.", aarav)])
    # Blocked
    _mktask("Vendor contract review", mum, mum_sales, sana, "Blocked",
        history=[("create", "created this task and assigned it to Sana Kapoor", priya),
                 ("status", "changed status to Blocked", sana)])
    # Done
    _mktask("Weekly Mumbai sales report", mum, mum_sales, vikram, "Done",
        history=[("create", "created this task and assigned it to Vikram Rao", priya),
                 ("status", "changed status to Done", vikram)])
    # Transferred (Priya -> Sana -> Vikram) then In progress
    _mktask("Onboard new Mumbai client", mum, mum_sales, vikram, "In progress",
        history=[("create", "created this task and assigned it to Sana Kapoor", priya),
                 ("transfer", "transferred from Sana Kapoor to Vikram Rao", sana),
                 ("status", "changed status to In progress", vikram)])

    # ---- Ahmedabad ----
    # Open
    _mktask("Set up Ahmedabad warehouse audit", ahm, ahm_sales, neha, "Open",
        history=[("create", "created this task and assigned it to Neha Patel", rahul)])
    # In progress
    _mktask("Ahmedabad pipeline sync", ahm, ahm_sales, sana, "In progress",
        history=[("create", "created this task and assigned it to Sana Kapoor", kabir),
                 ("status", "changed status to In progress", sana)])
    # Blocked
    _mktask("Resolve delivery delay — Surat route", ahm, ahm_sales, neha, "Blocked",
        history=[("create", "created this task and assigned it to Neha Patel", rahul),
                 ("status", "changed status to Blocked", neha)])
    # Done
    _mktask("Ahmedabad monthly recon", ahm, ahm_sales, vikram, "Done",
        history=[("create", "created this task and assigned it to Vikram Rao", rahul),
                 ("status", "changed status to Done", vikram)])
    # Transferred (Rahul -> Neha -> Sana), still Open
    _mktask("Prepare Ahmedabad expansion deck", ahm, ahm_sales, sana, "Open",
        history=[("create", "created this task and assigned it to Neha Patel", rahul),
                 ("transfer", "transferred from Neha Patel to Sana Kapoor", neha)])

    frappe.db.commit()
    total = frappe.db.count("SiteOps Task")
    print("=== Tasks seeded ===")
    print("Total tasks:", total)
    for s in ["Open", "In progress", "Blocked", "Done"]:
        print(f"  {s}: {frappe.db.count('SiteOps Task', {'status': s})}")
    print("Transferred tasks: 2 (one per site) — visible via the 'Transferred' badge + Activity timeline")
