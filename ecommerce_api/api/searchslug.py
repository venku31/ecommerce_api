
import frappe

@frappe.whitelist()
def get_searchslug(item_group=None):
    if item_group:
        return frappe.db.sql(f""" SELECT item_name,route,item_group from `tabWebsite Item` where item_group = '%(item_group)s' """ %{"item_group": item_group}, as_dict=True)
    else :
        return frappe.db.sql(f""" SELECT item_name,route,item_group from `tabWebsite Item` """ , as_dict=True)