# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _
from frappe.utils import flt


def execute(filters=None):
	columns, data = [], []

	columns = get_columns()
	data = get_data(filters)

	if not data:
		msgprint(_("No records found"))
		return columns,data

	return columns, data


def get_columns():
# 	Item Batch Days Date wise OB Recpt Issue CB Rate Amount
	return [
		{
			"fieldname": "item",
			"label":_("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"width":"350"
		},
		{
			"fieldname": "batch",
			"label":_("Batch"),
			"fieldtype": "Link",
			"options": "Batch",
			"width":"200"
		},
		{
			"fieldname": "days",
			"label":_("Days"),
			"fieldtype": "Data",
			"width":"200"
		},
		{
			"fieldname": "datewise",
			"label":_("Date wise"),
			"fieldtype": "Datetime",
			"width":"200"
		},
		{
			"fieldname": "opening_balance",
			"label":_("Opening Balance"),
			"fieldtype": "Float",
			"width":"200"
		},
		{
			"fieldname": "recevied",
			"label":_("Recpt"),
			"fieldtype": "Float",
			"width":"200"
		},
		{
			"fieldname": "issue",
			"label":_("Issue"),
			"fieldtype": "Float",
			"width":"200"
		},
		{
			"fieldname": "closing_balance",
			"label":_("Closing Balance"),
			"fieldtype": "Float",
			"width":"200"
		},
		{
			"fieldname": "rate",
			"label":_("Rate"),
			"fieldtype": "Currency",
			"width":"200"
		},
		{
			"fieldname": "amount",
			"label":_("Amount"),
			"fieldtype": "Currency",
			"width":"200"
		},
	]

def get_data(filters):
	return [{"item":""}]
	