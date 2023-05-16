import frappe


@frappe.whitelist()
def get_products(product=None):
    price_list = frappe.db.get_single_value("Ecommerce API Settings","default_price_list")
#     if product:
#         return frappe.db.sql(f""" SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
# (select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock,
# (select price_list_rate from `tabItem Price` where item_code=`tabWebsite Item`.item_code and price_list='%(price_list)s' and uom=`tabWebsite Item`.stock_uom) as price
# from `tabWebsite Item` where item_code='%(product)s' """ %{"product": product,"price_list":price_list}, as_dict=True)
#     else :
#         return frappe.db.sql(f""" SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
# (select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock,
# (select price_list_rate from `tabItem Price` where item_code=`tabWebsite Item`.item_code and price_list='%(price_list)s' and uom=`tabWebsite Item`.stock_uom) as price
# from `tabWebsite Item` """ %{"price_list":price_list} , as_dict=True)
    if product:
        return frappe.db.sql(f""" SELECT a.name,a.web_item_name,a.item_code,a.stock_uom,a.website_image,a.thumbnail,a.website_warehouse,a.item_group,a.web_long_description,a.short_description,a.route,a.ranking,a.stock_balance,a.item_price,
b.title as pricing_rule,b.apply_on,b.min_qty,b.max_qty,b.min_amt,b.max_amt,b.same_item,b.free_item,b.free_qty,b.discount_percentage,b.discount_amount
FROM
(SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
(select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock_balance,
(select price_list_rate from `tabItem Price` where item_code=`tabWebsite Item`.item_code and price_list='%(price_list)s' and uom=`tabWebsite Item`.stock_uom) as item_price
from `tabWebsite Item`)a
LEFT JOIN
(Select pr.title,pritem.item_code,pr.apply_on,pr.min_qty,pr.max_qty,pr.min_amt,pr.max_amt,pr.same_item,pr.free_item,pr.free_qty,pr.discount_percentage,pr.discount_amount
from `tabPricing Rule` pr LEFT JOIN `tabPricing Rule Item Code` pritem ON(pr.name=pritem.parent) where pr.disable=0 and pr.valid_upto>=CURDATE())b
ON (a.item_code=b.item_code) where a.item_code='%(product)s' """ %{"product": product,"price_list":price_list}, as_dict=True)
    else :
        return frappe.db.sql(f"""SELECT a.name,a.web_item_name,a.item_code,a.stock_uom,a.website_image,a.thumbnail,a.website_warehouse,a.item_group,a.web_long_description,a.short_description,a.route,a.ranking,a.stock_balance,a.item_price,
b.title as pricing_rule,b.apply_on,b.min_qty,b.max_qty,b.min_amt,b.max_amt,b.same_item,b.free_item,b.free_qty,b.discount_percentage,b.discount_amount
FROM
(SELECT name,web_item_name,item_name,item_code,stock_uom,website_image,thumbnail,website_warehouse,item_group,web_long_description,short_description,route,ranking,
(select actual_qty from `tabBin` where item_code=`tabWebsite Item`.item_code and stock_uom=`tabWebsite Item`.stock_uom and warehouse=`tabWebsite Item`.website_warehouse) as stock_balance,
(select price_list_rate from `tabItem Price` where item_code=`tabWebsite Item`.item_code and price_list='%(price_list)s' and uom=`tabWebsite Item`.stock_uom) as item_price
from `tabWebsite Item`)a
LEFT JOIN
(Select pr.title,pritem.item_code,pr.apply_on,pr.min_qty,pr.max_qty,pr.min_amt,pr.max_amt,pr.same_item,pr.free_item,pr.free_qty,pr.discount_percentage,pr.discount_amount
from `tabPricing Rule` pr LEFT JOIN `tabPricing Rule Item Code` pritem ON(pr.name=pritem.parent) where pr.disable=0 and pr.valid_upto>=CURDATE())b
ON (a.item_code=b.item_code) """ %{"price_list":price_list} , as_dict=True)