import frappe
from ecommerce_api.utils import error_response, success_response, get_access_level, get_allowed_categories, get_allowed_brands, get_child_categories
import json
from frappe.model.db_query import DatabaseQuery
from frappe.utils.global_search import search
from frappe.utils import flt, cint, today, add_days
from ecommerce_api.api.utils import (check_brand_exist, get_filter_list, 
                                       get_slide_images, get_stock_info, 
									   get_processed_list, get_item_field_values, 
									   get_field_names, create_user_tracking)

# Whitelisted Function
def get_list(kwargs):
	try:
		create_user_tracking(kwargs, "Product Listing")
		internal_call = kwargs.get("internal", 0)
		category_slug = kwargs.get('category')
		page_no = cint(kwargs.get('page_no', 1)) - 1
		limit = kwargs.get('limit', 20)
		filter_list = kwargs.get('filter')
		field_filters = kwargs.get("field_filters")
		or_filters = kwargs.get("or_filters")
		price_range = kwargs.get('price_range')
		search_text = kwargs.get('search_text')
		if kwargs.get('customer_id'):
			customer_id = kwargs.get('customer_id')
		elif frappe.session.user != "Guest":
			customer_id = frappe.db.get_value(
				"Customer", {"email": frappe.session.user}, 'name')
		else:
			customer_id = None
		access_level = get_access_level(customer_id)
		if not search_text:
			filter_args = {"access_level": access_level}
			if category_slug:
				child_categories = get_child_categories(category_slug)
				filter_args["category"] = child_categories
			if kwargs.get('brand'):
				filter_args["brand"] = frappe.get_value(
					'Brand', {'slug': kwargs.get('brand')})
			if kwargs.get('item'):
				filter_args["name"] = frappe.get_value(
					'Item', {'name': kwargs.get('item')})
			filters = get_filter_list(filter_args)
			type = 'brand-product' if check_brand_exist(filters) else 'product'
			if field_filters:
				field_filters = json.loads(field_filters)
				for value in field_filters.values():
					if len(value) == 2 and value[0] == 'like':
						value[1] = f"%{value[1]}%"
				filters.update(field_filters)
			if or_filters:
				or_filters = json.loads(or_filters)
				for value in or_filters.values():
					if len(value) == 2 and value[0] == 'like':
						value[1] = f"%{value[1]}%"
			if filter_list:
				filter_list = json.loads(filter_list)
				filters = append_applied_filters(filters, filter_list)
			debug = kwargs.get("debug_query", 0)
			count, data = get_list_data(
				filters, price_range, None, page_no, limit, or_filters=or_filters, debug = debug)
		else:
			type = 'product'
			global_items = search(search_text, doctype='Item')
			count, data = get_list_data({}, None, global_items, page_no, limit)
		result = get_processed_list(data, customer_id, type)
		total_count = count
		if internal_call:
			return result
		return {'msg': 'success', 'data': result, 'total_count': total_count}
	except Exception as e:
		frappe.logger('product').exception(e)
		return error_response(e)

# Whitelisted Function
def get_variants(kwargs):
	try:
		slug = kwargs.get('item')
		item_code = frappe.get_value('Item', {'slug': slug})
		filters = {'item_code': item_code}
		variant_list = get_variant_details(filters)
		variant_info = get_variant_info(variant_list)
		default_size = get_default_variant(item_code, "size")
		default_colour = get_default_variant(item_code, "colour")
		size = list({var.get('size') for var in variant_info if var.get('size')})
		sorted_size = frappe.get_all("Item Attribute Value",{"attribute_value":["in",size], "parent": "Size"},pluck='attribute_value', order_by="idx asc")
		colour = list({var.get('colour') for var in variant_info if var.get('colour')})
		stock_len = len([var.get('stock') for var in variant_info if var.get('stock')])
		attributes = []
		if size:
			attributes.append({
				"field_name": "size", 
				"label": "Select Size", 
				"values": sorted_size, 
				"default_value": default_size, 
				"display_thumbnail": variant_thumbnail_reqd(item_code, "size")
			})
		if colour:
			attributes.append({
				"field_name": "colour",
				"label": "Select Colour",
				"values": colour,
				"default_value": default_colour,
				"display_thumbnail": variant_thumbnail_reqd(item_code, "colour")
			})
		attr_dict = {'item_code': item_code,
					 'variants': get_variant_info(variant_list),
					 'attributes': attributes}
		return success_response(data=attr_dict)
	except Exception as e:
		frappe.logger('product').exception(e)
		return error_response(e)

# Whitelisted Function

def get_details(kwargs):
	try:
		create_user_tracking(kwargs, "Product Detail")
		item_slug = kwargs.get('item')
		if not item_slug:
			return error_response("Invalid key 'item'")
		customer_id = kwargs.get('customer_id') or frappe.db.get_value("Customer", {"email": frappe.session.user}, 'name') if frappe.session.user != "Guest" else None
		filters = get_filter_list({'slug': item_slug, 'access_level': get_access_level(customer_id)})
		count, item = get_list_data(filters, None, None, None, limit=1)
		field_names = get_field_names('Details')
		processed_items = []
		if item:
			item_fields = get_item_field_values(item, customer_id, field_names,None)
			processed_items.append(item_fields)
		return {'msg': 'success', 'data': processed_items}
	except Exception as e:
		frappe.logger('product').exception(e)
		return error_response(e)


# Whitelisted Function
def get_cyu_categories(kwargs):
	ignore_permissions = frappe.session.user == "Guest"
	return frappe.get_list('CYU Categories',
							   filters={},
							   fields=['name as product_category', 'image as product_img', 'slug', 'url as category_url', 'description'],
							   order_by='sequence',
							   ignore_permissions=ignore_permissions)


def get_categories(kwargs):
	filters = {
		"enable_category": "Yes"
	}
	ignore_perm = frappe.session.user == "Guest"
	return frappe.get_list('Category',
							   filters=filters,
							   fields=['name as category', 'image', 'slug', 'url as category_url', 'description'],
							   ignore_permissions=ignore_perm)


def get_top_categories(kwargs):
	categories = get_cyu_categories(kwargs)
	limit = int(kwargs.get('limit', 3))
	if limit and len(categories) > limit:
		categories = categories[:limit]
	res = []
	for category in categories:
		data = {
			"container": {
				"container_name": category.get("product_category"),
				"slug": category.get("slug"),
				"banner_img": category.get("product_img"),
				"banner_description": category.get("description"),
			}}
		kwargs['category'] = category.get('slug')
		kwargs['internal'] = 1
		kwargs['limit'] = 8
		p_list = get_list(kwargs)
		data['product_list'] = p_list
		res.append(data)
	return success_response(res)


def get_list_data(filters, price_range, global_items, page_no, limit, or_filters={}, debug = 0):
	offset = flt(page_no)*flt(limit)
	if 'access_level' not in filters:
		filters['access_level'] = 0

	if categories := get_allowed_categories(filters.get("category")):
		filters["category"] = ["in", categories]
	if brands := get_allowed_brands():
		if not (filters.get("brand") and filters.get("brand") in brands):
			filters["brand"] = ["in", brands]

	if global_items is not None:
		return get_items_via_search(global_items, filters)

	ignore_permissions = frappe.session.user == "Guest"
	order_by = 'valuation_rate asc' if price_range != 'high_to_low' else 'valuation_rate desc' if price_range else ''
	data = frappe.get_list('Item',
						   filters=filters,
						   or_filters=or_filters,
						   fields="*",
						   limit_page_length=limit,
						   limit_start=offset,
						   order_by=order_by,
						   ignore_permissions=ignore_permissions, debug=debug)
	count = get_count("Item", filters=filters, or_filters=or_filters,
					  ignore_permissions=ignore_permissions)
	if limit==1:
		data=data[0] if data else []
	return count, data


def get_count(doctype, **args):
	distinct = "distinct " if args.get("distinct") else ""
	args["fields"] = [f"count({distinct}`tab{doctype}`.name) as total_count"]
	res = DatabaseQuery(doctype).execute(**args)
	data = res[0].get("total_count")
	return data


def get_items_via_search(global_items, filters):
	item_list = []
	items = [item.name for item in global_items]
	filters['name'] = ["in", items]
	ignore_permission = bool(frappe.session.user == "Guest")
	item_list = frappe.get_list(
		'Item', filters, '*', ignore_permissions=ignore_permission)
	return len(item_list), item_list


# Get Variants Helper Functions
def get_variant_details(filters):
	ignore_perm = frappe.session.user == "Guest"
	return frappe.get_list('Item', {'variant_of': filters.get('item_code')}, ignore_permissions=ignore_perm)
	

def get_variant_size(item_code):
	return frappe.get_value('Item Variant Attribute',
							{'parent': item_code, 'attribute': 'Size'}, 'attribute_value')


def get_variant_colour(item_code):
	colour = frappe.get_value('Item Variant Attribute',
							  {'parent': item_code, 'attribute': 'Colour'}, 'attribute_value')
	return frappe.get_value('Item Attribute Value', {'attribute_value': colour}, 'abbr')


def get_variant_info(variant_list):
	return [{
			'variant_code': item.name,
			'size': get_variant_size(item.name),
			'colour': get_variant_colour(item.name),
			'stock': True if get_stock_info(item.name, 'stock_qty') != 0 else False,
			'image': get_slide_images(item.name, False)
			} for item in variant_list]

def get_default_variant(item_code, attribute):
	attr = frappe.get_value("Item Variant Attribute", {"variant_of": item_code, "is_default":1, "attribute": attribute},"attribute_value")
	return frappe.get_value('Item Attribute Value', {'attribute_value': attr}, 'abbr')

def variant_thumbnail_reqd(item_code, attribute):
	res = frappe.get_value("Item Variant Attribute", {"parent": item_code, "display_thumbnail":1, "attribute": attribute},"name")
	return bool(res)

def append_applied_filters(filters, filter_list):
	section_list = filter_list.get('sections')
	for section in section_list:
		# for key in section.items():
		doc_name = frappe.db.get_value('Filter Section Setting', {
			'filter_section_name': section['name']}, 'doctype_name')
		if doc_name == 'Item':
			field_val = frappe.db.get_value('Filter Section Setting', {
				'filter_section_name': section['name']}, 'field')
			# filters.append(["Item", field_val, "in", section['value']])
			filters.update({field_val: ['in', section['value']]})
	return filters


def get_recommendation(kwargs):
	# ptype = ["Equivalent", "Suggested", "Mandatory", "Alternate"]
	if kwargs.get("item_code"):
		item_code = kwargs.get("item_code")
	elif kwargs.get('item'):
		item_code = frappe.get_value('Item', {'slug': kwargs.get('item')})
	else:
		return error_response("invalid argument 'item'")
	fieldnames = ['item_code_1', 'item_code_2', 'item_code_3', 'item_code_4', 'item_code_5',
				  'item_code_6', 'item_code_7', 'item_code_8', 'item_code_9', 'item_code_10',
				  'item_code_11', 'item_code_12', 'item_code_13', 'item_code_14', 'item_code_15',
				  'item_code_16', 'item_code_17', 'item_code_18', 'item_code_19', 'item_code_20']
	if kwargs.get('ptype') == "Suggested":
		condition = f"item_code_1 = '{item_code}'"
	else:
		condition = ' or '.join([f'{field} = "{item_code}"' for field, item_code in zip(
			fieldnames, [item_code]*len(fieldnames))])
	items = frappe.db.sql(
		f"""select {', '.join(fieldnames)} from `tabMatching Items` where type = '{kwargs.get('ptype','')}' and ({condition})""", as_list=True)
	res = []
	if items:
		for item in items:
			for code in item:
				if code and code not in res:
					res.append(code)
		items = res
		if kwargs.get("item_only"):
			return items
		items.remove(item_code)
	else:
		if kwargs.get("item_only"):
			return []
		return error_response("No match found")
	result = get_detailed_item_list(items, kwargs.get("customer_id"))
	return success_response(data=result)


def get_product_url(item_detail):
	if not item_detail:
		return "/"
	item_cat = item_detail.get('category')
	item_cat_slug = frappe.db.get_value('Category',item_cat,'slug')
	if product_template:=item_detail.get("variant_of"):
		product_slug = frappe.db.get_value('Item', product_template, 'slug')
	else:
		product_slug = item_detail.get("slug")
	from ecommerce_api.api.v1.mega_menu import get_item_url
	return get_item_url('product', item_cat_slug, product_slug)


def get_item(item_code, size, colour):  # for cart
	variant_list = get_variant_details({'item_code': item_code})
	variants = get_variant_info(variant_list)
	if size and colour:
		item_code = [i.get('variant_code') for i in variants if i.get('size') == size and i.get('colour') == colour]
	elif size:
		item_code = [i.get('variant_code') for i in variants if i.get('size') == size]
	elif colour:
		item_code = [i.get('variant_code') for i in variants if i.get('colour') == colour]
	else:
		item_code = [item_code]
	return item_code[0] if item_code else []


def get_tagged_products(kwargs):
	try:
		if not kwargs.get('tag'):
			return error_response("key missing 'tag'")
		items = frappe.get_list("Tags MultiSelect", {"tag": kwargs.get(
			'tag')}, pluck='parent', ignore_permissions=True)
		res = get_detailed_item_list(items, kwargs.get("customer_id"))
		return success_response(data=res)
	except Exception as e:
		frappe.logger('product').exception(e)
		return error_response(e)


def get_detailed_item_list(items, customer_id=None, filters={}):
	access_level = get_access_level(customer_id)
	filter = {"name": ["in", items], "access_level": access_level}
	if filters:
		filter.update(filters)
	if not customer_id:
		customer_id = frappe.db.get_value(
			"Customer", {"email": frappe.session.user}, 'name')
	data = frappe.get_list(
		'Item', filter, "*", ignore_permissions=True)
	result = get_processed_list(data, customer_id, "product") 
	return result


def check_availability(kwargs):
	# params: item_code
	if frappe.session.user == "Guest":
		return error_response("Please login first")
	item_code = kwargs.get("item_code")
	if not item_code:
		return error_response("item_code missing")

	req_qty = flt(kwargs.get("qty", 1))
	stock_qty = flt(get_stock_info(
		item_code, "stock_qty", with_future_stock=False))

	qty = min(req_qty, stock_qty)
	template_item_code, lead_days = frappe.db.get_value(
		"Item", item_code, ["variant_of", "lead_time_days"])

	warehouse = frappe.db.get_value(
		"Website Item", {"item_code": item_code}, "website_warehouse")
	if not warehouse and template_item_code and template_item_code != item_code:
		warehouse = frappe.db.get_value(
			"Website Item", {"item_code": template_item_code}, "website_warehouse")

	future_stock = frappe.get_list("Item Future Availability", {'item': item_code,
																'date': [">", frappe.utils.today()],
																"quantity": [">", 0]}, "warehouse, date, quantity", order_by="date", ignore_permissions=True)

	res = []
	data = {
		"warehouse": warehouse,
		"qty": qty,
		"date": today(),
		"incoming_qty": 0,
		"incoming_date": ''
	}

	if req_qty <= stock_qty:
		return success_response(data=[data])

	req_qty -= stock_qty
	for row in future_stock:
		if req_qty <= 0:
			break

		qty = min(req_qty, row.get("quantity"))
		req_qty -= qty

		if row.get("warehouse") == data["warehouse"] and not data["incoming_qty"]:
			data.update(
				{"incoming_qty": qty, "incoming_date": row.get("date")})
		else:
			res.append({
				"warehouse": row.get("warehouse"),
				"incoming_qty": qty,
				"incoming_date": row.get("date")
			})

	res = [data] + res
	if req_qty > 0:
		res[-1].update({
			"additional_qty": req_qty,
			"available_on": add_days(today(), lead_days)
		})

	return success_response(data=res)


def get_web_item_future_stock(item_code, item_warehouse_field, warehouse=None):
	in_stock, stock_qty = 0, ""
	template_item_code, is_stock_item = frappe.db.get_value(
		"Item", item_code, ["variant_of", "is_stock_item"]
	)
	if not warehouse:
		warehouse = frappe.db.get_value(
			"Website Item", {"item_code": item_code}, item_warehouse_field)

	if not warehouse and template_item_code and template_item_code != item_code:
		warehouse = frappe.db.get_value(
			"Website Item", {
				"item_code": template_item_code}, item_warehouse_field
		)
	if warehouse:
		stock_qty = frappe.db.sql(
			"""
			select sum(quantity)
			from `tabItem Future Availability`
			where date >= CURDATE() and item=%s and warehouse=%s""",
			(item_code, warehouse),
		)

		if stock_qty:
			return stock_qty[0][0]
