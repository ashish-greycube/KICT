# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _
from frappe.utils import flt,getdate
from frappe.utils.dateutils import datetime_in_user_format
from frappe.utils import add_days, cstr, date_diff, getdate,add_to_date,cint,get_datetime
from pypika import functions as fn

def get_columns(filters):
# 	Item Batch Days Date wise OB Recpt Issue CB Rate Amount
	return [
		{
			"fieldname": "item_code",
			"label":_("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"width":"300"
		},
		# {
		# 	"fieldname": "customer",
		# 	"label":_("Customer"),
		# 	"fieldtype": "Link",
		# 	"options": "Customer",
		# 	"width":"150"
		# },
		{
			"fieldname": "batch_no",
			"label":_("Batch"),
			"fieldtype": "Link",
			"options": "Batch",
			"width":"150"
		},
		{
			"fieldname": "day_count",
			"label":_("Days"),
			"fieldtype": "Data",
			"width":"50"
		},
		{
			"fieldname": "datewise",
			"label":_("Date wise"),
			"fieldtype": "Datetime",
			"width":"180"
		},
		{
			"fieldname": "opening_qty",
			"label":_("Opening Balance"),
			"fieldtype": "Float",
			"width":"130"
		},
		{
			"fieldname": "in_qty",
			"label":_("Recpt"),
			"fieldtype": "Float",
			"width":"130"
		},
		{
			"fieldname": "out_qty",
			"label":_("Issue"),
			"fieldtype": "Float",
			"width":"130"
		},
		{
			"fieldname": "bal_qty",
			"label":_("Closing Balance"),
			"fieldtype": "Float",
			"width":"130"
		},
		{
			"fieldname": "rate",
			"label":_("Rate"),
			"fieldtype": "Currency",
			"width":"130"
		},
		{
			"fieldname": "amount",
			"label":_("Amount"),
			"fieldtype": "Currency",
			"width":"130"
		},
		{
			"fieldname": "remark",
			"label":_("Remark"),
			"fieldtype": "Data",
			"width":"130"
		},		
	]

def get_data(filters):
	return

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	
	return columns, data

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_unique_customer_list(doctype, txt, searchfield, start, page_len, filters):
	vessel = filters.get("vessel")
	return frappe.get_all(
		"Vessel Details",
		parent_doctype="Vessel",
		filters={"parent": vessel},
		fields=["distinct customer_name"],
		as_list=1,
	)

@frappe.whitelist()
def get_unique_customer_to_set(vessel):
	return frappe.get_all(
		"Vessel Details",
		parent_doctype="Vessel",
		filters={"parent": vessel},
		fields=["distinct customer_name"],
		as_list=1,
	)