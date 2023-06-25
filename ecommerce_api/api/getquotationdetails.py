import frappe

@frappe.whitelist(allow_guest=True)
def getquotationdetails(party):
    return frappe.db.sql(f"""select a.name,a.party_name as customer,a.customer_name,a.order_type,a.status,a.address_display,a.transaction_date,a.company,a.currency,a.selling_price_list,b.item_code,b.item_name,b.uom,
    b.qty,b.rate,b.amount,b.description,b.conversion_factor,b.base_rate,b.base_amount
    from `tabQuotation` a left join `tabQuotation Item` b
    ON (a.name = b.parent) where a.party_name=%(party)s """ %{"party":party}, as_dict=True)