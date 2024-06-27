# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def get_columns(filters):
	return [
		{
			"fieldname": "vessel",
			"label":_("Vessel"),
			"fieldtype": "Link",
			"options": "Vessel",
			"width":"200"
		},		
		{
			"fieldname": "customer",
			"label":_("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width":"200"
		},
		{
			"fieldname": "customer_item",
			"label":_("Customer Item"),
			"fieldtype": "Link",
			"options": "Item",
			"width":"200"
		},		
		{
			"fieldname": "received_qty",
			"label":_("Received Qty"),
			"fieldtype": "Float",
			"width":"150"
		},
		{
			"fieldname": "dispatch_qty",
			"label":_("Dispatch Qty"),
			"fieldtype": "Float",
			"width":"150"
		},
		{
			"fieldname": "handling_loss_audit_shortage",
			"label":_("Handling Loss / Audit Shortage"),
			"fieldtype": "Float",
			"width":"150"
		},
		{
			"fieldname": "balance",
			"label":_("Balance"),
			"fieldtype": "Float",
			"width":"150"
		},
		
	]

def get_data(filters):
	return

def execute(filters=None):
	# columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data
