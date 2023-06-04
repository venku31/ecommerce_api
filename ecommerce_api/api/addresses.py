
import frappe

@frappe.whitelist(allow_guest=True)
def addresses():
    return frappe.db.sql(f""" Select a.name,a.customer_name,a.customer_group,a.territory,a.tax_id,d.address_type,d.address_line1,d.address_line2,d.city,d.state,d.country,d.county,d.pincode,d.email_id,d.phone from
    (Select * from `tabCustomer`)a
    left join
    (Select * from
    ((Select name,address_type,address_line1,address_line2,city,state,country,county,pincode,email_id,phone From `tabAddress`)b
    left join
    (Select parent,link_name,link_doctype From `tabDynamic Link` where link_doctype="Customer" and parenttype="Address")c
    ON b.name=c.parent))d ON a.name=d.link_name""", as_dict=True)