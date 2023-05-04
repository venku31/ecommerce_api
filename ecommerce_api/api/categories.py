import frappe


@frappe.whitelist()
def get_categories(item_group=None):
    if item_group:
        return frappe.db.sql(f""" SELECT name,item_group_name as item_group,image from `tabItem Group` where is_group=0 and name = '%(item_group)s' """ %{"item_group": item_group}, as_dict=True)
    else :
        return frappe.db.sql(f""" SELECT name,item_group_name as item_group,image from `tabItem Group` where is_group=0 """ , as_dict=True)