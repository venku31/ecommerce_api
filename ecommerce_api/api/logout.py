import json
import frappe
from frappe import auth

@frappe.whitelist(allow_guest=True)
def logout():
    try:
        login_manager = frappe.auth.LoginManager()
        user = frappe.session.user
        # login_manager = LoginManager()
        login_manager.logout(user=user)
        # return generate_response("S", "200", message="Logged Out")
        return "Logout Success"
    except Exception as e:
        raise Exception(e)