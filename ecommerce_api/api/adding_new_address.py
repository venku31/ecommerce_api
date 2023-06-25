import frappe
import json

@frappe.whitelist(allow_guest=True)
def adding_new_address(data=None):
    data=json.loads(frappe.request.data)
    customer= frappe.get_value("Customer",data.get("customer"),'name')
    # print("/////////////",customer)
    # addr = frappe.new_doc("Address")
    # addr.address_title = customer
    # addr.address_type = data.get("address_type")
    # addr.address_line1 = data.get("address_line1")
    # addr.address_line2 = data.get("address_line2")
    # addr.city = data.get("city")
    # addr.state = data.get("state")
    # addr.pincode = data.get("postal_code")
    # addr.country = data.get("country")
    # addr.phone = data.get("phone")
    # addr.email = data.get("email")
    # addr.is_primary_address = 1
    # addr.is_shipping_address = 1
    # # addr.append("links", {"parentfield": "links","parenttype": "Address","idx": 1,"link_doctype": "Customer", "link_name": data.get("customer")})
    # addr.links: [{"parentfield": "links","parenttype": "Address","link_doctype" : "Customer", "link_name" : customer,"link_title" : customer,"doctype": "Dynamic Link"}]
    # try:
    #     addr.flags.ignore_mandatory = True
    #     addr.flags.ignore_permissions= True
    #     addr.save(ignore_permissions=True)
    #     return addr
    # except Exception as e:
    #     frappe.log_error(title="Error saving Address", message=e)
    
    try:
        address_name = frappe.get_doc(
        {
            "doctype": "Address",
            "address_title": data.get("customer"),
            "address_type": data.get("address_type"),
            "address_line1": data.get("address_line1") or "Address 1",
            "address_line2": data.get("address_line2"),
            "city": data.get("city"),
            "state": data.get("state"),
            "pincode": data.get("postal_code"),
            "country": data.get("country"),
            "phone": data.get("phone"),
            "email_id": data.get("email"),
            "links": [{"link_doctype": "Customer", "link_name": data.get("customer")}],
            }
        ).insert(ignore_permissions=True)
        return address_name
            # address_name = address_name.name
    except Exception as e:
        frappe.log_error(title="Error saving Address", message=e)
    # return address_name