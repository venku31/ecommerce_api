import frappe

@frappe.whitelist()
def get_home_page_top_picks(product=None):
    if product:
        return frappe.db.sql(f""" SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
(select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock
from `tabWebsite Item` where item_code='%(product)s' and website_top_pick=1 """ %{"product": product}, as_dict=True)
    else :
        return frappe.db.sql(f""" SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
(select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock
from `tabWebsite Item` where website_top_pick=1 """ , as_dict=True)

@frappe.whitelist()
def get_home_page_new_products(product=None):
    if product:
        return frappe.db.sql(f""" SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
(select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock
from `tabWebsite Item` where item_code='%(product)s' and website_new_product=1 """ %{"product": product}, as_dict=True)
    else :
        return frappe.db.sql(f""" SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
(select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock
from `tabWebsite Item` where website_new_product=1 """ , as_dict=True)

@frappe.whitelist()
def get_home_page_new_products():
    return frappe.db.sql(f""" SELECT parent as Website_item_name,offer_title,offer_subtitle,offer_details,offer_image from `tabWebsite Offer` """ , as_dict=True)