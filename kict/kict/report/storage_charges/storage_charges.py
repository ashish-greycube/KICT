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
	if not filters:
		filters = {}
	
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
	# initialize variables
	sc_row= frappe._dict({})
	sc_data = []
	loop=1
	previous_batch_no=None
	previous_batch_count=0
	previous_show_date=None
	to_date = getdate(filters.to_date)
	real_previous_date=None
	result_length=len(data)

	for d in data:
		# case 1 : repeat batch
		if previous_batch_no==d['batch_no']:
			print(d['batch_no'],d['show_date']==previous_show_date,d['show_date'],previous_show_date,d.actual_qty)
			# case 1A : repeat batch but date is not the next data, so create dummy repeat data
			if d['show_date']!=previous_show_date:
				# dummy data till matching batch date of incoming
				next_date=add_days(previous_show_date,1)
				while next_date <  d['show_date']:
				# sequential data
					sc_row= frappe._dict({})
					sc_row.item_code=d['item_code']
					sc_row.batch_no=d['batch_no']
					sc_row.datewise=next_date
					if custom_is_holiday_applicable_for_free_storage_days==1 and (next_date in holiday_list_days and previous_batch_count <custom_free_storage_days):
						sc_row.day_count='H'
						sc_row.remark=get_holiday_description(next_date)
						previous_batch_count=previous_batch_count
					else:
						sc_row.day_count=previous_batch_count+1
						previous_batch_count=sc_row.day_count
					sc_row.opening_qty=previous_balance_qty
					sc_row.in_qty=0
					sc_row.out_qty=0
					sc_row.bal_qty=previous_balance_qty
					sc_row.rate=0
					sc_row.storage_item_name=''
					sc_row.amount=0
					if sc_row.day_count!='H' and cint(sc_row.day_count)>=first_slot_from_days and cint(sc_row.day_count)<=first_slot_to_days:
						sc_row.rate=get_item_price(first_slot_item,sc_row.datewise) or 0
						sc_row.storage_item_name=first_slot_item
						sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
					elif sc_row.day_count!='H' and cint(sc_row.day_count)>=second_slot_from_days:
						sc_row.rate=get_item_price(second_slot_item,sc_row.datewise) or 0
						sc_row.storage_item_name=second_slot_item
						sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
					sc_data.append(sc_row)
					next_date=add_days(next_date,1)
					previous_show_date=next_date
				# case when entry is side by side date, i.e. 1st and 2nd
				previous_show_date=next_date
				
			# case 1B : repeat batch and incoming date is matching, so real data 
			if d['show_date']==previous_show_date:
				print(d['show_date']==previous_show_date,d['show_date'],previous_show_date,d.actual_qty)
				sc_row= frappe._dict({})
				sc_row.item_code=d['item_code']
				sc_row.batch_no=d['batch_no']
				sc_row.datewise=d['show_date']
				if custom_is_holiday_applicable_for_free_storage_days==1 and (d['show_date'] in holiday_list_days and previous_batch_count <custom_free_storage_days):
					sc_row.day_count='H'
					sc_row.remark=get_holiday_description(d['show_date'])
					previous_batch_count=previous_batch_count
				else:
					# it is same day in and out, so not increasing day count	
					if (real_previous_date==d['show_date']):
						sc_row.day_count=previous_batch_count
					else:
						sc_row.day_count=previous_batch_count+1
					previous_batch_count=sc_row.day_count			
				sc_row.opening_qty=previous_balance_qty
				sc_row.in_qty=flt(d.actual_qty, float_precision) if flt(d.actual_qty) > 0 else 0
				sc_row.out_qty=abs(flt(d.actual_qty, float_precision))	 if flt(d.actual_qty) < 0 else 0
				sc_row.bal_qty=flt(sc_row.opening_qty+flt(d.actual_qty, float_precision),float_precision)
				sc_row.rate=0
				sc_row.storage_item_name=''
				sc_row.amount=0
				if sc_row.day_count!='H' and cint(sc_row.day_count)>=first_slot_from_days and cint(sc_row.day_count)<=first_slot_to_days:
					sc_row.rate=get_item_price(first_slot_item,sc_row.datewise) or 0
					sc_row.storage_item_name=first_slot_item
					sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
				elif sc_row.day_count!='H' and cint(sc_row.day_count)>=second_slot_from_days:
					sc_row.rate=get_item_price(second_slot_item,sc_row.datewise) or 0
					sc_row.storage_item_name=second_slot_item
					sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
				sc_data.append(sc_row)
				previous_batch_no=d['batch_no']
				previous_balance_qty=sc_row.bal_qty
				previous_show_date=d['show_date']
				# use for dummy
				previous_opening_qty=sc_row.opening_qty
				previous_in_qty=sc_row.in_qty
				previous_out_qty=sc_row.out_qty				

		# case 2 : new batch
		elif previous_batch_no!=d['batch_no']:
			#  case 2A: new batch but there is dummy pending for PB as bal is not zero, so stretch till to date
			if previous_show_date and previous_show_date < to_date and previous_balance_qty>0:
				# dummy data till to date as balance is not zero
				next_date=add_days(previous_show_date,1)
				while next_date <= to_date:
				# sequential data
					sc_row= frappe._dict({})
					sc_row.item_code=previous_item_code
					sc_row.batch_no=previous_batch_no				
					sc_row.datewise=next_date
					if custom_is_holiday_applicable_for_free_storage_days==1 and (next_date in holiday_list_days and previous_batch_count <custom_free_storage_days):
						sc_row.day_count='H'
						sc_row.remark=get_holiday_description(next_date)
						previous_batch_count=previous_batch_count
					else:
						sc_row.day_count=previous_batch_count+1
						previous_batch_count=sc_row.day_count					
					sc_row.opening_qty=previous_balance_qty
					sc_row.in_qty=0
					sc_row.out_qty=0
					sc_row.bal_qty=previous_balance_qty
					sc_row.rate=0
					sc_row.storage_item_name=''
					sc_row.amount=0
					if sc_row.day_count!='H' and cint(sc_row.day_count)>=first_slot_from_days and cint(sc_row.day_count)<=first_slot_to_days:
						sc_row.rate=get_item_price(first_slot_item,sc_row.datewise) or 0
						sc_row.storage_item_name=first_slot_item
						sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
					elif sc_row.day_count!='H' and cint(sc_row.day_count)>=second_slot_from_days:
						sc_row.rate=get_item_price(second_slot_item,sc_row.datewise) or 0
						sc_row.storage_item_name=second_slot_item
						sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
					sc_data.append(sc_row)
					next_date=add_days(next_date,1)

			# new batch
			previous_batch_count=0
			sc_row= frappe._dict({})
			sc_row.item_code=d['item_code']
			sc_row.batch_no=d['batch_no']
			sc_row.datewise=d['show_date']
			sc_row.day_count=1
			if custom_is_holiday_applicable_for_free_storage_days==1 and (d['show_date'] in holiday_list_days and previous_batch_count <=custom_free_storage_days):
				sc_row.day_count='H'
				sc_row.remark=get_holiday_description(d['show_date'])
				previous_batch_count=previous_batch_count
			else:
				sc_row.day_count=previous_batch_count+1
				previous_batch_count=sc_row.day_count				
			
			sc_row.opening_qty=0
			sc_row.in_qty=flt(d.actual_qty, float_precision) if flt(d.actual_qty) > 0 else 0
			sc_row.out_qty=abs(flt(d.actual_qty, float_precision))	 if flt(d.actual_qty) < 0 else 0
			sc_row.bal_qty=flt(sc_row.opening_qty+flt(d.actual_qty, float_precision),float_precision)
			sc_row.rate=0
			sc_row.storage_item_name=''
			sc_row.amount=0
			if sc_row.day_count!='H' and cint(sc_row.day_count)>=first_slot_from_days and cint(sc_row.day_count)<=first_slot_to_days:
				sc_row.rate=get_item_price(first_slot_item,sc_row.datewise) or 0
				sc_row.storage_item_name=first_slot_item
				sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
			elif sc_row.day_count!='H' and cint(sc_row.day_count)>=second_slot_from_days:
				sc_row.rate=get_item_price(second_slot_item,sc_row.datewise) or 0
				sc_row.storage_item_name=second_slot_item
				sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
			sc_data.append(sc_row)
			
		
			previous_batch_no=d['batch_no']
			previous_balance_qty=sc_row.bal_qty
			previous_show_date=d['show_date']
			# use for dummy
			previous_opening_qty=sc_row.opening_qty
			previous_in_qty=sc_row.in_qty
			previous_out_qty=sc_row.out_qty
			#  use for dummy and to date filler
			previous_item_code=d['item_code']

		if loop==result_length:
			# last raw is reached
			#  new batch but is dummy pending for PB as bal is not zero
			if previous_show_date and previous_show_date < to_date and previous_balance_qty>0:
				# dummy data till to date as balance is not zero
				next_date=add_days(previous_show_date,1)
				while next_date <= to_date:
				# sequential data
					sc_row= frappe._dict({})
					sc_row.item_code=previous_item_code
					sc_row.batch_no=previous_batch_no				
					sc_row.datewise=next_date
					if custom_is_holiday_applicable_for_free_storage_days==1 and (next_date in holiday_list_days and previous_batch_count <custom_free_storage_days):
						sc_row.day_count='H'
						sc_row.remark=get_holiday_description(next_date)
						previous_batch_count=previous_batch_count
					else:
						sc_row.day_count=previous_batch_count+1
						previous_batch_count=sc_row.day_count					
					sc_row.opening_qty=previous_balance_qty
					sc_row.in_qty=0
					sc_row.out_qty=0
					sc_row.bal_qty=previous_balance_qty
					sc_row.rate=0
					sc_row.storage_item_name=''
					sc_row.amount=0
					if sc_row.day_count!='H' and cint(sc_row.day_count)>=first_slot_from_days and cint(sc_row.day_count)<=first_slot_to_days:
						sc_row.rate=get_item_price(first_slot_item,sc_row.datewise) or 0
						sc_row.storage_item_name=first_slot_item
						sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
					elif sc_row.day_count!='H' and cint(sc_row.day_count)>=second_slot_from_days:
						sc_row.rate=get_item_price(second_slot_item,sc_row.datewise) or 0
						sc_row.storage_item_name=second_slot_item
						sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
					sc_data.append(sc_row)
					next_date=add_days(next_date,1)
		loop=loop+1
		real_previous_date=d['show_date']
	return columns, sc_data


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
	# 1st query is of received
	# 2nd query is of out
	query = frappe.db.sql(
		"""
			select 
				sle.name,
				sle.vessel,
				sle.item_code,
				batch_package.batch_no,	
				item.customer,
				sle.posting_time,
				case 
					when (sle.posting_time > '06:00:00'	and sle.posting_time <= '23:59:59')	then  sle.posting_date
					else date_add(sle.posting_date, INTERVAL -1 DAY)  
				end as show_date,				
				sum(batch_package.qty) as actual_qty,
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
			group by
				sle.vessel,
				item.customer,
				sle.item_code,
				batch_package.batch_no,
				show_date
UNION 
			select 
				sle.name,
				sle.vessel,
				sle.item_code,
				batch_package.batch_no,
				item.customer,
				sle.posting_time,				
				case 
					when (sle.posting_date <= '2024-10-31') then sle.posting_date
					when (sle.posting_time > '06:00:00'	and sle.posting_time <= '23:59:59')	then  sle.posting_date
					else date_add(sle.posting_date, INTERVAL -1 DAY)  
				end as show_date,				
				sum(batch_package.qty) as actual_qty,
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
			group by
				sle.vessel,
				item.customer,
				sle.item_code,
				batch_package.batch_no,
				show_date
order by vessel ,item_code ,manufacturing_date,show_date,posting_time,name		
		
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


def get_item_price(item_code,transacion_date=None):
	from erpnext.stock.get_item_details import get_price_list_rate_for
	args=frappe._dict({
		'price_list':"Standard Selling",
		'qty':1,
		'uom':frappe.db.get_value('Item', item_code, 'stock_uom'),
		"transaction_date":transacion_date})
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