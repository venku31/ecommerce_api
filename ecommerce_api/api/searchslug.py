
import frappe

@frappe.whitelist()
def get_searchslug(item_name=None):
    if item_name:
        return frappe.db.sql(f""" SELECT item_name,route from `tabWebsite Item` where item_name = '(item_name)s' """ %{"item_name": item_name}, as_dict=True)
    else :
        return frappe.db.sql(f""" SELECT item_name,route from `tabWebsite Item` """ , as_dict=True)