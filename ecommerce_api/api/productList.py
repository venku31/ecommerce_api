import frappe


@frappe.whitelist()
def get_products(product=None):
    if product:
        return frappe.db.sql(f""" SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
(select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock
from `tabWebsite Item` where item_code='%(product)s' """ %{"product": product}, as_dict=True)
    else :
        return frappe.db.sql(f""" SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
(select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock
from `tabWebsite Item` """ , as_dict=True)