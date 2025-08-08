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
			"fieldname": "sle_name",
			"label":_("SLE"),
			"fieldtype": "Link",
			"options": "Stock Ledger Entry",
			"width":"110"
		},		
		{
			"fieldname": "voucher_no",
			"label":_("Voucher"),
			"fieldtype": "Data",
			"width":"190"
		},
		{
			"fieldname": "voucher_type",
			"label":_("Voucher Type"),
			"fieldtype": "Data",
			"width":"190"
		},		
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
		# {
		# 	"fieldname": "day_count",
		# 	"label":_("Days"),
		# 	"fieldtype": "Data",
		# 	"width":"50"
		# },
		{
			"fieldname": "sedate",
			"label":_("SE Date"),
			"fieldtype": "Datetime",
			"width":"180"
		},
		{
			"fieldname": "datewise",
			"label":_("Date wise"),
			"fieldtype": "Date",
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
		# {
		# 	"fieldname": "rate",
		# 	"label":_("Rate"),
		# 	"fieldtype": "Currency",
		# 	"width":"130"
		# },
		# {
		# 	"fieldname": "amount",
		# 	"label":_("Amount"),
		# 	"fieldtype": "Currency",
		# 	"width":"130"
		# },
		# {
		# 	"fieldname": "remark",
		# 	"label":_("Remark"),
		# 	"fieldtype": "Data",
		# 	"width":"130"
		# },		
	]

def get_holiday_description(holiday_date):
	terminal_holiday_list = frappe.db.get_single_value('Coal Settings', 'terminal_holiday_list')
	description=''
	description=frappe.get_all(
							"Holiday",
							fields=["description"],
							filters={"parent": terminal_holiday_list,"holiday_date":holiday_date},
							order_by="holiday_date",							
							limit=1
						)
	if len(description)>0:
		description=description[0].description
	return description

def execute(filters=None):

	
	
	terminal_holiday_list = frappe.db.get_single_value('Coal Settings', 'terminal_holiday_list')
	holiday_list_days = [
				getdate(d[0])
				for d in frappe.get_all(
					"Holiday",
					fields=["holiday_date"],
					filters={"parent": terminal_holiday_list},
					order_by="holiday_date",
					as_list=1,
				)
			]
	if not filters:
		filters = {}
	columns = get_columns(filters)
	customer=filters.get("customer")
	custom_storage_charge_based_on = frappe.db.get_value('Customer', customer, 'custom_storage_charge_based_on')
	if custom_storage_charge_based_on=='Fixed Days':
		frappe.msgprint("Report is not applicable for customer having storage charge based on Fixed Days")
		return columns,[]
	

	if custom_storage_charge_based_on=='Actual Storage Days':
		first_slot_storage_charges=0
		second_slot_storage_charges=0		
		
		custom_free_storage_days=cint(frappe.db.get_value('Customer', customer, 'custom_free_storage_days'))
		custom_is_holiday_applicable_for_free_storage_days=cint(frappe.db.get_value('Customer', customer, 'custom_is_holiday_applicable_for_free_storage_days'))
		customer_doc=frappe.get_doc('Customer',customer)
		if len(customer_doc.get("custom_chargeable_storage_charges_slots_details"))>0:
			first_slot_from_days=cint(customer_doc.custom_chargeable_storage_charges_slots_details[0].from_days)
			first_slot_to_days=cint(customer_doc.custom_chargeable_storage_charges_slots_details[0].to_days)
			first_slot_item=customer_doc.custom_chargeable_storage_charges_slots_details[0].item
			first_slot_storage_charges = get_item_price(first_slot_item) or 0
			if len(customer_doc.get("custom_chargeable_storage_charges_slots_details"))>1:
				second_slot_from_days=cint(customer_doc.custom_chargeable_storage_charges_slots_details[1].from_days)
				# second_slot_to_days=cint(customer_doc.custom_chargeable_storage_charges_slots_details[1].to_days)
				second_slot_item=customer_doc.custom_chargeable_storage_charges_slots_details[1].item
				second_slot_storage_charges = get_item_price(second_slot_item) or 0				
		
	float_precision = cint(frappe.db.get_default("float_precision")) or 3
	data=get_stock_ledger_entries_for_batch_bundle(filters)

	sc_data = []
	starting_opening_balance = 0
	previous_row_item = None
	float_precision = cint(frappe.db.get_default("float_precision")) or 3
	for d in data:
		if d.voucher_type == "Delivery Note":
			rake_dispatch_name = frappe.db.get_value("Delivery Note",d.voucher_no,"custom_rcn")
			d.voucher_type = rake_dispatch_name
		elif d.voucher_type == "Stock Entry":
			stock_entry_type = frappe.db.get_value("Stock Entry",d.voucher_no,"stock_entry_type")
			d.voucher_type = stock_entry_type
		if previous_row_item == None or previous_row_item == d.item_code:
			d["opening_qty"] = starting_opening_balance
			starting_opening_balance =flt(( starting_opening_balance + d.in_qty + d.out_qty),float_precision)
			d["bal_qty"] = starting_opening_balance
			previous_row_item = d.item_code
			print(d)
		else :
			starting_opening_balance = 0
			d["opening_qty"] = starting_opening_balance
			starting_opening_balance = flt(( starting_opening_balance + d.in_qty + d.out_qty),float_precision)
			d["bal_qty"] = starting_opening_balance
			previous_row_item = d.item_code
			print(d,"---d")
		sc_data.append(d)
	return columns,sc_data


# def get_dates(filters):
# 	from_date = getdate(filters.from_date)
# 	to_date = getdate(filters.to_date)

# 	"""get list of dates in between from date and to date"""
# 	no_of_days = date_diff( to_date,from_date)
# 	print('no_of_days',no_of_days)
# 	dates = [{'datewise':add_days(add_to_date(from_date,hours=6), i),'day_count':i+1} for i in range(0, no_of_days+1)]
# 	return dates

def get_stock_ledger_entries_for_batch_bundle(filters):
	conditions = get_conditions(filters)
	query = frappe.db.sql(
		"""
			select 
				sle.name as sle_name,
				sle.voucher_no,
				sle.voucher_type,
				sle.vessel,
				sle.item_code,
				batch_package.batch_no,	
				item.customer,
				sle.posting_datetime as sedate,
				case 
					when (sle.posting_time > '06:00:00'
					and sle.posting_time <= '23:59:59')
						then  sle.posting_date
					else date_add(sle.posting_date, INTERVAL -1 DAY)  
				end as datewise,				
				batch_package.qty as in_qty,
				0 as out_qty,
				manufacturing_date
			from
				`tabStock Ledger Entry` sle
			inner join `tabSerial and Batch Entry` batch_package
			on
				sle.serial_and_batch_bundle = batch_package.parent
			inner join `tabBatch` batch 
			on batch_package.batch_no =batch.name 
			inner join `tabItem` item
			on item.name=sle.item_code
			where
				sle.docstatus < 2
				and sle.is_cancelled = 0
				and sle.has_batch_no = 1
				and actual_qty >0
			 {0}
UNION 
			select 
				sle.name as sle_name,
				sle.voucher_no,
				sle.voucher_type,
				sle.vessel,
				sle.item_code,
				batch_package.batch_no,
				item.customer,
				sle.posting_datetime as sedate,
				sle.posting_date as datewise,
				0 as in_qty,
				batch_package.qty as out_qty,
				manufacturing_date
			from
				`tabStock Ledger Entry` sle
			inner join `tabSerial and Batch Entry` batch_package
			on
				sle.serial_and_batch_bundle = batch_package.parent
			inner join `tabBatch` batch 
			on batch_package.batch_no =batch.name 
			inner join `tabItem` item
			on item.name=sle.item_code			
			where
				sle.docstatus < 2
				and sle.is_cancelled = 0
				and sle.has_batch_no = 1
				and actual_qty <0
			{0}
order by vessel ,item_code ,manufacturing_date,datewise,sle_name			
		
""".format(conditions),filters,as_dict=1,debug=1)	
	return query


def get_conditions(filters):
	conditions =""

	if filters.vessel:
		conditions += " and sle.vessel = %(vessel)s"

	if filters.customer:
		conditions += " and item.customer = %(customer)s"

	first_line_ashore=frappe.db.get_value('Statement of Fact', filters.vessel, 'first_line_ashore')
	if not first_line_ashore:
		frappe.throw(_("First line ashore is required in SOF for the vessel"))

	if filters.get("from_date") and filters.get("to_date"):
		if getdate(filters.get("to_date")) < getdate(first_line_ashore):
			frappe.throw(_("To date {0} should be greater then first line ashore {1}".format(filters.get("to_date"),getdate(first_line_ashore))))
		if filters.get("to_date") < filters.get("from_date"):	
			frappe.throw(_("To Date should be greater then From Date"))

		if filters.get("to_date") >= filters.get("from_date"):
			conditions += " and sle.posting_date between '{0}' and '{1}'".format(filters.get("from_date"),filters.get("to_date"))


	if filters.customer_item:
		conditions += " and sle.item_code = %(customer_item)s"

	if filters.batch_no:
		conditions += " and batch_package.batch_no = %(batch_no)s"

	return conditions


def get_item_price(item_code):
	from erpnext.stock.get_item_details import get_price_list_rate_for
	args=frappe._dict({
		'price_list':"Standard Selling",
		'qty':1,
		'uom':frappe.db.get_value('Item', item_code, 'stock_uom')})
	return get_price_list_rate_for(args,item_code)		


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