import frappe
from frappe.utils import random_string

# sport_network.utils.check_user_exists


def check_user_exists(email):
	"""
	Check if a user with the provied Email. exists
	"""
	return frappe.db.exists('User', email)


def success_response(data=None, id=None):
	response = {'msg': 'success'}
	response['data'] = data
	if id:
		response['data'] = {'id': id, "name": id}
	return response


def error_response(err_msg):
	# frappe.log_error(frappe.get_traceback(), 'Api Error')
	return {
		'msg': 'error',
		'error': err_msg
	}


def resync_cart(session):
	"""
	Resync User Session Cart With Logged In User Cart
	Delete Session Cart After Transfering Items To User Cart.
	"""
	try:
		if name := frappe.db.exists('Quotation', {'owner': session, "status": "Draft"}):
			data = {"owner": frappe.session.user}
			if customer := frappe.db.exists("Customer", {"email": frappe.session.user}):
				data["party_name"] = customer

			if existing_doc := frappe.db.exists("Quotation", {"owner": frappe.session.user, "status": "Draft"}):
				# items = frappe.get_list("Quotation Item", {"parent":name},["item_code", "qty"])
				items = frappe.db.sql(
					f"select item_code, qty from `tabQuotation Item` where parent = '{name}'", as_dict=True)
				doc = frappe.get_doc("Quotation", existing_doc)

				for item in items:
					quotation_items = doc.get(
						"items", {"item_code": item.item_code})
					if not quotation_items:
						doc.append("items", {
							"doctype": "Quotation Item",
							"item_code": item.item_code,
							"qty": item.qty
						})
					else:
						quotation_items[0].qty = item.qty

				if customer and not doc.party_name:
					doc.party_name = customer
				doc.flags.ignore_permissions = True
				doc.save()
				frappe.delete_doc('Quotation', name, ignore_permissions=True)

			else:
				frappe.db.set_value("Quotation", name, data)
				frappe.db.commit()

			# Delete  user
			frappe.delete_doc(
				'User', session, ignore_permissions=True, force=True)
			return "success"

		return {"msg": "no quotation Found", "session": session, "f_session": frappe.session}
	except Exception as e:
		frappe.logger('utils').exception(e)
		return


def send_mail(template_name, recipients, context):
	frappe.sendmail(
		recipients=recipients,
		subject=frappe.render_template(
			frappe.db.get_value(
				"Email Template", template_name, "subject"
			),
			context,
		),
		cc="",
		bcc="",
		delayed=False,
		message=frappe.render_template(
			frappe.db.get_value(
				"Email Template", template_name, "response"
			),
			context,
		),
		reference_doctype="",
		reference_name="",
		attachments="",
		print_letterhead=False,
	)
	return "Email Sent"


def create_temp_user():
	frappe.local.login_manager.login_as("Administrator")
	username = random_string(8)
	usr = frappe.get_doc({
		"doctype": "User",
		"email": username+"@random.com",
		"first_name": "TGuest",
		"send_welcome_email": 0
	}).insert()
	usr.add_roles("Customer")
	frappe.local.login_manager.login_as(usr.email)
	return usr.email


def update_customer(customer=None, data={}):
	if customer:
		doc = frappe.get_doc("Customer", customer)
		doc.update(data).save()
	else:
		doc = frappe.get_doc({
			"doctype": "Customer",
			"customer_group": "Customer",
			"customer_type": "Individual",
			"territory": "All Territories",
		}).update(data).insert(ignore_permissions=True)
	return doc.name


def get_company_address(company):
	from frappe.contacts.doctype.address.address import get_default_address
	ret = frappe._dict()
	ret.company_address = get_default_address("Company", company)
	ret.gstin = frappe.db.get_value("Address", ret.company_address, 'gstin')

	return ret


def sync_contact(old_id, new_id):
	frappe.local.login_manager.login_as("Administrator")
	if temp := frappe.db.exists("Contact", {"user": old_id}):
		frappe.delete_doc("Contact", temp)
	contact = frappe.get_doc("Contact", {"email_id": new_id})
	contact.user = new_id
	contact.save()


@frappe.whitelist()
def sync_guest_user(email):
	if "random" in frappe.session.user:
		temp = frappe.session.user
		frappe.rename_doc("User", frappe.session.user, email)
		sync_contact(temp, email)
		frappe.local.login_manager.login_as(email)
	else:
		return


def check_guest_user(email=frappe.session.user):
	return 'random' in email


@frappe.whitelist(allow_guest=True)
def download_pdf(
	doctype, name, format=None, doc=None, no_letterhead=0, language=None, letter_head=None
):
	from frappe.utils.print_format import download_pdf
	download_pdf(doctype, name, format=format,
				 doc=doc, no_letterhead=no_letterhead)


def autofill_slug(doc, method=None):
	if hasattr(doc, 'slug') and not doc.get('slug'):
		doc.slug = frappe.utils.slug(doc.name)


def get_access_level(customer_id=None):
	if customer_id:
		grp = frappe.db.get_value("Customer", customer_id, 'customer_group')
		access_level = frappe.db.get_value(
			"Customer Group", grp, "access_level") or 0
		return access_level
	return 0

def get_allowed_categories(category_list = []):
	categories = []
	user = frappe.session.user
	if user != "Guest":
		cust = frappe.db.get_value("Customer", {"email": user}, [
								   "name", "customer_group"], as_dict=1)
		if cust:
			categories = frappe.db.get_values(
				"Category Multiselect", {"parent": cust["name"]}, "name1", pluck=1)
			if not categories and cust.get("customer_group"):
				categories = frappe.db.get_values(
					"Category Multiselect", {"parent": cust["customer_group"]}, "name1", pluck=1)
	if not categories:
		categories = frappe.db.get_values(
			"Category Multiselect", {"parent": "Web Settings"}, "name1", pluck=1)
	allowed_categories = []
	for category in categories:
		allowed_categories += get_child_categories(category,True,True)
	filtered_category = []
	if allowed_categories:
		if category_list:
			filtered_category = [category for category in allowed_categories if category in category_list]
	return filtered_category or (allowed_categories if categories else category_list)


def get_allowed_brands():
	brands = []
	user = frappe.session.user
	if user != "Guest":
		cust = frappe.db.get_value("Customer", {"email": user}, [
								   "name", "customer_group"], as_dict=1)
		if cust:
			brands = frappe.db.get_values(
				"Brand Multiselect", {"parent": cust["name"]}, "name1", pluck=1)
			if not brands and cust.get("customer_group"):
				brands = frappe.db.get_values(
					"Brand Multiselect", {"parent": cust["customer_group"]}, "name1", pluck=1)
	if not brands:
		brands = frappe.db.get_values(
			"Brand Multiselect", {"parent": "Web Settings"}, "name1", pluck=1)
	return brands


def make_payment_entry(sales_order):
	invoice = frappe.db.get_value(
		'Sales Invoice', {'sales_order': sales_order}, 'name')
	if invoice:
		dt = 'Sales Invoice'
		dn = invoice
	else:
		dt = 'Sales Order'
		dn = sales_order
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	from frappe.utils import getdate
	payment_entry_doc = get_payment_entry(dt, dn)
	payment_entry_doc.reference_no = sales_order
	payment_entry_doc.reference_date = getdate()
	payment_entry_doc.save(ignore_permissions=True)
	payment_entry_doc.submit()

def get_parent_categories(category, is_name = False, excluded = [], name_only = False):
	filters = category if is_name else {"slug":category} 
	cat = frappe.db.get_value("Category", filters, ['lft','rgt'], as_dict=1)
	if not (cat and category):
		return []
	excluded_cat = "', '".join(excluded)
	parent_categories = frappe.db.sql(
		f"""select name, slug, parent_category from `tabCategory`
		where lft <= %s and rgt >= %s
		and enable_category='Yes' and name not in ('{excluded_cat}')
		order by lft asc""",
		(cat.lft, cat.rgt),
		as_dict=True,
	)
	if name_only:
		return [row.name for row in parent_categories] if parent_categories else []
	return parent_categories

def get_child_categories(category, is_name = False, with_parent = False):
	filters = category if is_name else {"slug":category} 
	cat = frappe.db.get_value("Category", filters, ['lft','rgt'], as_dict=1)
	category_list = []
	if not (cat and filters):
		return []
	child_categories = frappe.db.sql(
		"""select name, slug, parent_category from `tabCategory`
		where lft >= %s and rgt <= %s
		and enable_category='Yes'
		order by lft asc""",
		(cat.lft, cat.rgt),
		as_dict=True,
	)
	category_list = [child.name for child in child_categories]
	if category_list and with_parent:
		for category in category_list:
			category_list += get_parent_categories(category, True, category_list, True)
	return category_list