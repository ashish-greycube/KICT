# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _
from frappe.utils import flt,getdate
from frappe.utils.dateutils import datetime_in_user_format
from frappe.utils import add_days, cstr, date_diff, getdate,add_to_date,cint
from pypika import functions as fn

# def execute(filters=None):
# 	columns, data = [], []

# 	columns = get_columns()
# 	data = get_data(filters)

# 	if not data:
# 		msgprint(_("No records found"))
# 		return columns,data

# 	return columns, data


def get_columns(filters):
# 	Item Batch Days Date wise OB Recpt Issue CB Rate Amount
	return [
		{
			"fieldname": "item_code",
			"label":_("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"width":"350"
		},
		{
			"fieldname": "batch_no",
			"label":_("Batch"),
			"fieldtype": "Link",
			"options": "Batch",
			"width":"200"
		},
		{
			"fieldname": "day_count",
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
			"fieldname": "opening_qty",
			"label":_("Opening Balance"),
			"fieldtype": "Float",
			"width":"200"
		},
		{
			"fieldname": "in_qty",
			"label":_("Recpt"),
			"fieldtype": "Float",
			"width":"200"
		},
		{
			"fieldname": "out_qty",
			"label":_("Issue"),
			"fieldtype": "Float",
			"width":"200"
		},
		{
			"fieldname": "bal_qty",
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

def execute(filters=None):

	if not filters:
		filters = {}
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))
	columns = get_columns(filters)
	float_precision = cint(frappe.db.get_default("float_precision")) or 3
	# data=get_dates(filters)
	data=get_stock_ledger_entries_for_batch_bundle(filters)
	
	# item_map = get_item_details(filters)
	# print(get_dates(filters))
	# iwb_map = get_item_warehouse_batch_map(filters, float_precision)
	# print('iwb_map---------------')
	# print(iwb_map)
	# print('iwb_map---------------')
	# data = []
	# for item in sorted(iwb_map):
	# 	if not filters.get("item") or filters.get("item") == item:
	# 		for batch in sorted(iwb_map[item]):
	# 			qty_dict = iwb_map[item][batch]
	# 			if qty_dict.opening_qty or qty_dict.in_qty or qty_dict.out_qty or qty_dict.bal_qty:
	# 				data.append(
	# 					[
	# 						item,
	# 						item_map[item]["item_name"],
	# 						item_map[item]["description"],
	# 						batch,
	# 						flt(qty_dict.opening_qty, float_precision),
	# 						flt(qty_dict.in_qty, float_precision),
	# 						flt(qty_dict.out_qty, float_precision),
	# 						flt(qty_dict.bal_qty, float_precision),
	# 						item_map[item]["stock_uom"],
	# 					]
	# 				)

	return columns, data


def get_dates(filters):
	from_date = getdate(filters.from_date)
	to_date = getdate(filters.to_date)

	"""get list of dates in between from date and to date"""
	no_of_days = date_diff( to_date,from_date)
	print('no_of_days',no_of_days)
	dates = [{'datewise':add_days(add_to_date(from_date,hours=6), i),'day_count':i+1} for i in range(0, no_of_days+1)]
	return dates

def get_stock_ledger_entries_for_batch_bundle(filters):
	conditions = get_conditions(filters)
	query = frappe.db.sql(
		"""
		select
			vessel,
			item_code,
			batch_no,
			six_date,
			actual_qty
		from
			(
			select 
				sle.vessel,
				sle.item_code,
				batch_package.batch_no,
				sum(batch_package.qty) as actual_qty,
				case 
					when (sle.posting_time >= '06:00:00'
					and sle.posting_time <= '24:00:00')
						then sle.posting_date
					else date_add(sle.posting_date, INTERVAL -1 DAY)
				end as six_date
			from
				`tabStock Ledger Entry` sle
			inner join `tabSerial and Batch Entry` batch_package
			on
				sle.serial_and_batch_bundle = batch_package.parent
			where
				sle.docstatus < 2
				and sle.is_cancelled = 0
				and sle.has_batch_no = 1
			{0}
			group by
				sle.vessel,
				sle.item_code,
				batch_package.batch_no,
				six_date
			order by
				sle.vessel,
				sle.item_code,
				batch_package.batch_no,
				six_date					
		) t
""".format(conditions),filters,as_dict=1,debug=1)	
	return query
	sle = frappe.qb.DocType("Stock Ledger Entry")
	batch_package = frappe.qb.DocType("Serial and Batch Entry")

	query = (
		frappe.qb.from_(sle)
		.inner_join(batch_package)
		.on(batch_package.parent == sle.serial_and_batch_bundle)
		.select(
			sle.item_code,
			batch_package.batch_no,
			sle.posting_date,
			sle.posting_datetime,
			fn.Sum(batch_package.qty).as_("actual_qty"),
		)
		.where(
			(sle.docstatus < 2)
			& (sle.is_cancelled == 0)
			& (sle.has_batch_no == 1)
			& (sle.posting_date <= filters["to_date"])
			& (sle.vessel == filters["vessel"])
		)
		.groupby(batch_package.batch_no)
		.orderby(sle.item_code)
	)


	for field in ["item_code", "batch_no", "company"]:
		if filters.get(field):
			if field == "batch_no":
				query = query.where(batch_package[field] == filters.get(field))
			else:
				query = query.where(sle[field] == filters.get(field))

	return query.run(as_dict=True) or []
	

def get_item_warehouse_batch_map(filters, float_precision):
	sle = get_stock_ledger_entries_for_batch_bundle(filters)
	iwb_map = {}

	from_date = getdate(filters["from_date"])
	to_date = getdate(filters["to_date"])
	print('sle-----')
	print(sle)
	print('---')
	for d in sle:
		iwb_map.setdefault(d.item_code, {}).setdefault(
			d.batch_no, frappe._dict({"opening_qty": 0.0, "in_qty": 0.0, "out_qty": 0.0, "bal_qty": 0.0})
		)
		qty_dict = iwb_map[d.item_code][d.batch_no]
		if d.posting_date < from_date:
			qty_dict.opening_qty = flt(qty_dict.opening_qty, float_precision) + flt(
				d.actual_qty, float_precision
			)
		elif d.posting_date >= from_date and d.posting_date <= to_date:
			if flt(d.actual_qty) > 0:
				qty_dict.in_qty = flt(qty_dict.in_qty, float_precision) + flt(d.actual_qty, float_precision)
			else:
				qty_dict.out_qty = flt(qty_dict.out_qty, float_precision) + abs(
					flt(d.actual_qty, float_precision)
				)

		qty_dict.bal_qty = flt(qty_dict.bal_qty, float_precision) + flt(d.actual_qty, float_precision)

	return iwb_map	

def get_item_details(filters):
	item_map = {}
	for d in (frappe.qb.from_("Item").select("name", "item_name", "description", "stock_uom")).run(as_dict=1):
		item_map.setdefault(d.name, d)

	return item_map


def get_conditions(filters):
	conditions =""

	if filters.vessel:
		conditions += " and sle.vessel = %(vessel)s"


	first_line_ashore=frappe.db.get_value('Statement of Fact', filters.vessel, 'first_line_ashore')
	first_line_ashore=datetime_in_user_format(first_line_ashore)
	if not first_line_ashore:
		frappe.throw(_("First line ashore is required in SOF for the vessel"))



	if filters.get("from_date") and filters.get("to_date"):
		print(type(first_line_ashore),type(filters.get("to_date")))
		if filters.get("to_date") < first_line_ashore:
			frappe.throw(_("To Date should be greater then First line ashore {0}".format(first_line_ashore)))
		if filters.get("to_date") < filters.get("from_date"):	
			frappe.throw(_("To Date should be greater then From Date"))

		if filters.get("to_date") >= filters.get("from_date"):
			conditions += " and sle.posting_date between '{0}' and '{1}'".format(filters.get("from_date"),filters.get("to_date"))


	if filters.customer_item:
		conditions += " and sle.item_code = %(customer_item)s"

	if filters.batch_no:
		conditions += " and batch_package.batch_no = %(batch_no)s"

	return conditions