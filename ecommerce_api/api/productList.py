import frappe


@frappe.whitelist()
def get_products(product=None):
    price_list = frappe.db.get_single_value("Ecommerce API Settings","default_price_list")
    if product:
        return frappe.db.sql(f""" SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
(select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock,
(select price_list_rate from `tabItem Price` where item_code=`tabWebsite Item`.item_code and price_list='%(price_list)s' and uom=`tabWebsite Item`.stock_uom) as price
from `tabWebsite Item` where item_code='%(product)s' """ %{"product": product,"price_list":price_list}, as_dict=True)
    else :
        return frappe.db.sql(f""" SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
(select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock,
(select price_list_rate from `tabItem Price` where item_code=`tabWebsite Item`.item_code and price_list='%(price_list)s' and uom=`tabWebsite Item`.stock_uom) as price
from `tabWebsite Item` """ %{"price_list":price_list} , as_dict=True)