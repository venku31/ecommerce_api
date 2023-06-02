import frappe
import json
from frappe import auth

@frappe.whitelist(allow_guest=True)
def create_user(data=None):
    data=json.loads(frappe.request.data)
    try:
        user = frappe.new_doc("User")
        user.first_name = data.get("first_name")
        user.email = data.get("email")
        user.enabled = 1
        user.send_welcome_email = 0
        user.thread_notify = 0
        user.mobile_no = data.get("mobile_no")
        user.new_password = data.get("password")
        user.user_type = data.get("user_type")
        user.flags.ignore_mandatory = True
        user.save(ignore_permissions=True)
        frappe.db.commit()
        # user2 = frappe.get_doc('User',user.name)
        # api_generate = generate_keys(user2)
        return {"User Successfully Created ":user.name}
    except Exception as e:
        return {"error":e}

@frappe.whitelist( allow_guest=True)
def generate_keys(user):
    # user = frappe.get_doc('User',frappe.session.user)
    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)

    if not user_details.api_key:
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key

    user_details.api_secret = api_secret
    user_details.save()

    return api_secret