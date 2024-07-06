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
			"precision":1,
			"width":"150"
		},
		{
			"fieldname": "dispatch_qty",
			"label":_("Dispatch Qty"),
			"fieldtype": "Float",
			"precision":1,
			"width":"150"
		},
		{
			"fieldname": "handling_loss_audit_shortage",
			"label":_("Loss/Short Qty"),
			"fieldtype": "Float",
			"precision":1,
			"width":"150"
		},
		{
			"fieldname": "balance",
			"label":_("Balance"),
			"fieldtype": "Float",
			"precision":1,
			"width":"150"
		},
		
	]

def get_data(filters):
	conditions = get_conditions(filters)
	query = frappe.db.sql(
		""" SELECT
					vd.parent vessel,
					vd.customer_name customer ,
					vd.item customer_item,
					vd.tonnage_mt received_qty,
					rrd.commercial_destination_item commercial_destination_item,
					IFNULL(sum(rrd.rr_item_weight_mt), 0) dispatch_qty
			FROM
					`tabVessel Details` vd
			left outer join `tabRailway Receipt Item Details` rrd on
					vd.parent = rrd.vessel
				and vd.item = rrd.commercial_destination_item
				and rrd.docstatus < 2
			group by
				rrd.commercial_destination_item
				{0}
""".format(conditions),filters,as_dict=1,debug=1)

	from kict.kict.doctype.vessel.vessel import get_qty_for_handling_loss_and_audit_shortage

	for d in query:
		handling_loss_audit_shortage_qty = get_qty_for_handling_loss_and_audit_shortage(d.vessel,d.customer_item)
		d["handling_loss_audit_shortage"] = handling_loss_audit_shortage_qty
		balance_qty = d.received_qty - d.dispatch_qty - (handling_loss_audit_shortage_qty or 0)
		d["balance"] = balance_qty or 0

	return query

def get_conditions(filters):
	conditions = ""
	if filters.customer:
		conditions += " where vd.customer_name = %(customer)s"
	
	return conditions

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	
	return columns, data
