import frappe
from ecommerce_api.utils import success_response
from erpnext.utilities.product import adjust_qty_for_expired_items
from frappe.utils import flt
from frappe.model.db_query import DatabaseQuery


def validate_pincode(kwargs):
	pincode = True if frappe.db.exists(
		'Delivery Pincode', kwargs.get('pincode')) else False
	return success_response(data=pincode)


def get_cities(kwargs):
	city_list = frappe.db.get_list('City', filters = {'state': kwargs.get('state')}, fields =['name', 'state', 'country'], ignore_permissions=True)
	return success_response(data=city_list)

def get_states(kwargs):
	state_list = frappe.db.get_list('State', filters = {}, fields =['name', 'country'], ignore_permissions=True)
	return success_response(state_list)


def get_countries(kwargs):
	country_list = frappe.db.get_list('Country', filters = {}, fields =['name as country_name'], ignore_permissions=True)
	return success_response(data = country_list)


def check_brand_exist(filters):
	return any('brand' in i for i in filters)


def get_filter_list(kwargs):
	filters = {
		"disabled": 0,
		"variant_of": ['is', "not set"]
	}
	for key, val in kwargs.items():
		if val:
			filters.update({key: val})
	return filters

def get_field_names(product_type):
    return frappe.db.get_all(
        'Product Fields',
        filters={'parent': frappe.get_value('Product Page Field', {'product_type': product_type})},
        pluck='field'
    )

def get_processed_list(items, customer_id, url_type = "product"):
    field_names = get_field_names('List')
    processed_items = []
    for item in items:
        item_fields = get_item_field_values(item, customer_id, field_names, url_type)
        processed_items.append(item_fields)
    return processed_items

def get_item_field_values(item, customer_id, field_names, url_type = "product"):
    computed_fields = {
        'image_url': lambda: {'image_url': get_slide_images(item.get('name'), True)},
        'status': lambda: {'status': 'template' if item.get('has_variants') else 'published'},
        'in_stock_status': lambda: {'in_stock_status': True if get_stock_info(item.get('name'), 'stock_qty') != 0 else False},
        'brand_img': lambda: {'brand_img': frappe.get_value('Brand', item.get('brand'), ['image']) or None},
        'mrp_price': lambda: {'mrp_price': get_item_price(item.get("name"), customer_id, get_price_list(customer_id))[1]},
        'price': lambda: {'price': get_item_price(item.get("name"), customer_id, get_price_list(customer_id))[0]},
        'display_tag': lambda: {'display_tag': item.get('display_tag') or frappe.get_list("Tags MultiSelect", {"parent": item.name}, pluck='tag', ignore_permissions=True)},
        'url': lambda: {'url': get_product_url(item, url_type)},
        'brand_video_url': lambda: {'brand_video_url': frappe.get_value('Brand', item.get('brand'), ['brand_video_link']) or None},
		'size_chart': lambda: {'size_chart': frappe.get_value('Size Chart', item.get('size_chart'), 'chart')},
		'slide_img': lambda: {'slide_img': get_slide_images(item.get('name'), False)},
		'features': lambda: {'features': get_features(item.key_features) if item.key_features else []},
		'why_to_buy': lambda: {'why_to_buy': frappe.db.get_value('Why To Buy', item.get("select_why_to_buy"), "name1")},
		'prod_specifications': lambda: {'prod_specifications': get_specifications(item)},
		'store_pick_up_available': lambda: {'store_pick_up_available': item.get('store_pick_up_available') == 'Yes'},
		'home_delivery_available': lambda: {'home_delivery_available': item.get('home_delivery_available') == 'Yes'}
    }
    item_fields = {}
    for field_name in field_names:
        if field_name in computed_fields.keys():
            item_fields.update(computed_fields.get(field_name)())
        else:
            item_fields.update({field_name: item.get(field_name)})
    return item_fields


def get_product_url(item_detail, url_type = "product"):
	if not item_detail:
		return "/"
	item_cat = item_detail.get('category')
	item_cat_slug = frappe.db.get_value('Category',item_cat,'slug')
	if product_template:=item_detail.get("variant_of"):
		product_slug = frappe.db.get_value('Item', product_template, 'slug')
	else:
		product_slug = item_detail.get("slug")
	from summit_api.api.v1.mega_menu import get_item_url
	return get_item_url(url_type, item_cat_slug, product_slug)


def get_price_list(customer=None):
	selling_settings = frappe.get_cached_value(
		"Web Settings", None, "default_price_list")
	if customer:
		cust = frappe.get_cached_value(
			"Customer", customer, ["default_price_list", "customer_group"], as_dict=True)
		cust_grp_pl = frappe.get_cached_value(
			"Customer Group", cust.get("customer_group"), "default_price_list")
		return cust.get("default_price_list") or cust_grp_pl or selling_settings
	return selling_settings

def get_item_price(item_name, customer_id=None, price_list=None, valuation_rate=0):
	filter = {
		'item_code': item_name,
		'price_list': price_list}

	if customer_id:
		filter['customer'] = customer_id
		price, mrp_price = frappe.db.get_value("Item Price", filter, ['price_list_rate', 'strikethrough_rate']) or (0,0)
		if price:
			return (price, mrp_price)

	filter['customer'] = ["is", "null"]
	price, mrp_price = frappe.get_value(
		'Item Price', filter, ['price_list_rate', 'strikethrough_rate']) or (0, 0)
	return (price, (mrp_price or valuation_rate))


def get_stock_info(item_code, key, with_future_stock=True):
	roles = frappe.get_roles(frappe.session.user)
	is_dealer = "Dealer" in roles
	warehouse_field = 'dealer_warehouse' if is_dealer else 'website_warehouse'
	variant_list = frappe.db.get_all('Item', {'variant_of': item_code}, 'name')
	if not variant_list:
		variant_list = frappe.db.get_all('Item', {'name': item_code}, 'name')
	stock = 0
	for variant in variant_list:
		stock_qty = get_web_item_qty_in_stock(
			variant.get('name'), warehouse_field).get(key)
		stock += flt(stock_qty)
		if with_future_stock:
			future_stock = get_web_item_future_stock(
				variant.get('name'), warehouse_field)
			stock += flt(future_stock)
	if key == 'stock_qty':
		return stock


def get_web_item_future_stock(item_code, item_warehouse_field, warehouse=None):
	stock_qty = 0
	template_item_code = frappe.db.get_value(
		"Item", item_code, ["variant_of"]
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


def get_web_item_qty_in_stock(item_code, item_warehouse_field, warehouse=None):
	in_stock, stock_qty = 0, ""
	total_qty = 0
	template_item_code, is_stock_item = frappe.db.get_value(
		"Item", item_code, ["variant_of", "is_stock_item"]
	)

	default_warehouse = frappe.get_cached_value("Web Settings", None, "default_warehouse")
	warehouses = [default_warehouse] if default_warehouse else []
	if not warehouse:
		warehouse = frappe.db.get_value("Website Item", {"item_code": item_code}, item_warehouse_field)


	if not warehouse and template_item_code and template_item_code != item_code:
		warehouse = frappe.db.get_value(
			"Website Item", {"item_code": template_item_code}, item_warehouse_field
		)
	if warehouse:
		warehouses.append(warehouse)
		stock_list = frappe.db.sql(
			f"""
			select GREATEST(S.actual_qty - S.reserved_qty - S.reserved_qty_for_production - S.reserved_qty_for_sub_contract, 0) / IFNULL(C.conversion_factor, 1),
			S.warehouse
			from tabBin S
			inner join `tabItem` I on S.item_code = I.Item_code
			left join `tabUOM Conversion Detail` C on I.sales_uom = C.uom and C.parent = I.Item_code
			where S.item_code='{item_code}' and S.warehouse in ('{"', '".join(warehouses)}')"""
		)
		
		if stock_list:
			for stock_qty in stock_list:
				stock_qty = adjust_qty_for_expired_items(item_code, [stock_qty], stock_qty[1])
				total_qty += stock_qty[0][0]
				if not in_stock:
					in_stock = stock_qty[0][0] > 0 and 1 or 0
		
	return frappe._dict(
		{"in_stock": in_stock, "stock_qty": total_qty, "is_stock_item": is_stock_item}
	)

def get_slide_images(item, tile_image):
	img = None if tile_image else []
	imgs = get_slideshow_value(item)
	if imgs:
		if slideshow := imgs.get("slideshow"):
			ss_doc = frappe.get_all('Website Slideshow Item', {
									 "parent": slideshow}, "*", order_by='idx asc')
			ss_images = [image.image for image in ss_doc]
			if ss_images:
				img = ss_images[0] if tile_image else ss_images
				return img
		if imgs.get('website_image'):
			img = imgs.get('website_image') if tile_image else [
				imgs.get('website_image')]
	return img


def get_slideshow_value(item_name):
	return frappe.get_value('Website Item', {'item_code': item_name}, ['slideshow', "website_image"], as_dict=True)

def get_features(key_feature):
	key_features = frappe.get_all(
		"Key Feature Detail", {"parent": key_feature}, pluck = "key_feature", order_by ="idx")
	feat_val = frappe.get_all("Key Feature",{"key_feature": ["in",key_features]}, ["key_feature as heading", "description"], order_by = "idx")
	return {'name': 'Key Features', 'values': feat_val}


def get_technologies_details(item):
    techs = frappe.get_list("Final Technology", {'parent': item.technologies}, pluck='technology', ignore_permissions=True, order_by="idx")
    lst = []
    for row in techs:
        name = frappe.db.get_value("Technology", row, "name")
        image = frappe.db.get_value("Technology", row, "image")
        description = frappe.db.get_value("Technology", row, "description")
        tech_details = {}
        tech_details['name'] = name
        tech_details['image'] = image
        tech_details['description'] = description
        technology_details = []
        
        tech_details_rows = frappe.get_all(
            "Technology Details",
            filters={'parent': name},
            fields=["title", "video_frame", "description", "image", "sequence"],
            order_by="idx ASC"
        )
        
        for tech_details_row in tech_details_rows:
            details = {}
            details['title'] = tech_details_row.title
            details['video_frame'] = tech_details_row.video_frame
            details['description'] = tech_details_row.description
            details['image'] = tech_details_row.image
            details['sequence'] = tech_details_row.sequence
            technology_details.append(details)
        
        tech_details['technology_details'] = technology_details
        lst.append(tech_details)
    return lst

def get_specifications(item):
	res = []
	item_filters = frappe.get_all("Item Filters", {"parent":item.name}, ["field_name","field_value"], order_by="idx")
	if item_filters:
		res.append({
			'name': 'Specifications',
			'values': get_specification_details(item_filters) if item_filters else []
		})
	if item.get("geometry_file"):
		res.append({
			'name': 'Geometry',
			'values': item.get("geometry_file")
		})
	if item.get("technologies"):
		res.append({
			'name': 'Technologies',
			'values': item.get("technologies"),
			'details': get_technologies_details(item)
		})
	return res

def get_specification_details(filters):
	return [
		{
			'name': tech.field_name,
			'values': tech.field_value
		}
		for tech in filters
	]
 
def create_user_tracking(kwargs, page):
	if frappe.session.user == "Guest":
		return
	doc = frappe.new_doc("User Tracking")
	doc.user = frappe.session.user
	doc.page = page
	doc.ip_address = frappe.local.request_ip
	for key, value in kwargs.items():
		if key in ["version", "method", "entity", "cmd"]:
			continue
		doc.append("parameters",{
			"key": key,
			"value": value
		})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()