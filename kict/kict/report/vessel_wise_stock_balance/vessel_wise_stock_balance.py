# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _

def get_columns(filters):
	return [
		{
			"fieldname": "vessel",
			"label":_("Vessel"),
			"fieldtype": "Link",
			"options": "Vessel",
			"width":"230"
		},		
		{
			"fieldname": "item_code",
			"label":_("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"width":"420"
		},		
		{
			"fieldname": "in_qty",
			"label":_("Recpt"),
			"fieldtype": "Float",
			"width":"150",
			"precision":1
		},		
		{
			"fieldname": "out_qty",
			"label":_("Issue"),
			"fieldtype": "Float",
			"width":"150",
			"precision":1
		},
		{
			"fieldname": "balance",
			"label":_("Balance"),
			"fieldtype": "Float",
			"precision":1,
			"width":"150"
		},		
		]

def get_stock_ledger_entries(filters):
	query = frappe.db.sql(
		"""SELECT a.vessel,a.item_code,a.in_qty,a.out_qty,a.in_qty+a.out_qty as balance from 
(select 
				sle.vessel,
				sle.item_code,
    sum(case when sle.actual_qty>0 then sle.actual_qty else 0 end) as in_qty, 
    sum(case when sle.actual_qty<0 then sle.actual_qty else 0 end) as out_qty
    from
				`tabStock Ledger Entry` sle
			where
				sle.docstatus < 2
				and sle.is_cancelled = 0
				and sle.has_batch_no = 1
				and sle.vessel is not null
			group by sle.vessel,sle.item_code 
order by vessel ,item_code )a
where a.in_qty+a.out_qty >0""",as_dict=1,debug=1)
	return query		

def execute(filters=None):
	# columns, data = [], []
	columns = get_columns(filters)
	data=get_stock_ledger_entries(filters)
	return columns, data


