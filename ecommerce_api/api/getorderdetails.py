import frappe

@frappe.whitelist(allow_guest=True)
def getorderdetails():
    return frappe.db.sql(f"""select a.name,a.customer,a.customer_name,a.order_type,a.status,a.address_display,a.transaction_date,a.delivery_date,a.company,a.currency,a.selling_price_list,b.item_code,b.item_name,b.uom,
    b.qty,b.rate,b.amount,b.description,b.conversion_factor,b.base_rate,b.base_amount
    from `tabSales Order` a left join `tabSales Order Item` b
    ON (a.name = b.parent) where a.docstatus=1 """, as_dict=True)