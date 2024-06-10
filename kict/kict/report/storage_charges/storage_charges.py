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
	]

def execute(filters=None):
	storage_charges_16_25_days = get_item_price(frappe.db.get_single_value('Coal Settings', 'storage_charges_16_25_days')) or 0
	storage_charges_beyond_26_days = get_item_price(frappe.db.get_single_value('Coal Settings', 'storage_charges_beyond_26_days')) or 0
	terminal_holiday_list = frappe.db.get_single_value('Coal Settings', 'terminal_holiday_list')
	holiday_list_days = [
				getdate(d[0])
				for d in frappe.get_all(
					"Holiday",
					fields=["holiday_date"],
					filters={"parent": terminal_holiday_list,"custom_only_applicable_for_customer_storage":1},
					order_by="holiday_date",
					as_list=1,
				)
			]
	if not filters:
		filters = {}
	columns = get_columns(filters)
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
	result_length=len(data)

	for d in data:
		# case 1 : repeat batch
		if previous_batch_no==d['batch_no']:
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
					if next_date in holiday_list_days and previous_batch_count <15:
						sc_row.day_count='H'
						previous_batch_count=previous_batch_count
					else:
						sc_row.day_count=previous_batch_count+1
						previous_batch_count=sc_row.day_count
					sc_row.opening_qty=previous_opening_qty
					sc_row.in_qty=previous_in_qty
					sc_row.out_qty=previous_out_qty
					sc_row.bal_qty=previous_balance_qty
					sc_row.rate=0
					sc_row.amount=0
					if sc_row.day_count!='H' and cint(sc_row.day_count)>=16 and cint(sc_row.day_count)<=25:
						sc_row.rate=storage_charges_16_25_days
						sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
					elif sc_row.day_count!='H' and cint(sc_row.day_count)>25:
						sc_row.rate=storage_charges_beyond_26_days
						sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
					sc_data.append(sc_row)
					next_date=add_days(next_date,1)
					previous_show_date=next_date
				
			# case 1B : repeat batch and incoming date is matching, so real data 
			if d['show_date']==previous_show_date:
				sc_row= frappe._dict({})
				sc_row.item_code=d['item_code']
				sc_row.batch_no=d['batch_no']
				sc_row.datewise=d['show_date']
				if d['show_date'] in holiday_list_days and previous_batch_count <15:
					sc_row.day_count='H'
					previous_batch_count=previous_batch_count
				else:
					sc_row.day_count=previous_batch_count+1
					previous_batch_count=sc_row.day_count				
				sc_row.opening_qty=previous_opening_qty
				sc_row.in_qty=flt(d.actual_qty, float_precision) if flt(d.actual_qty) > 0 else 0
				sc_row.out_qty=abs(flt(d.actual_qty, float_precision))	 if flt(d.actual_qty) < 0 else 0
				sc_row.bal_qty=sc_row.opening_qty+flt(d.actual_qty, float_precision)
				sc_row.rate=0
				sc_row.amount=0
				if sc_row.day_count!='H' and cint(sc_row.day_count)>=16 and cint(sc_row.day_count)<=25:
					sc_row.rate=storage_charges_16_25_days
					sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
				elif sc_row.day_count!='H' and cint(sc_row.day_count)>25:
					sc_row.rate=storage_charges_beyond_26_days
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
					if next_date in holiday_list_days and previous_batch_count <15:
						sc_row.day_count='H'
						previous_batch_count=previous_batch_count
					else:
						sc_row.day_count=previous_batch_count+1
						previous_batch_count=sc_row.day_count					
					sc_row.opening_qty=previous_opening_qty
					sc_row.in_qty=previous_in_qty
					sc_row.out_qty=previous_out_qty
					sc_row.bal_qty=previous_balance_qty
					sc_row.rate=0
					sc_row.amount=0
					if sc_row.day_count!='H' and cint(sc_row.day_count)>=16 and cint(sc_row.day_count)<=25:
						sc_row.rate=storage_charges_16_25_days
						sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
					elif sc_row.day_count!='H' and cint(sc_row.day_count)>25:
						sc_row.rate=storage_charges_beyond_26_days
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
			if d['show_date'] in holiday_list_days and previous_batch_count <=15:
				sc_row.day_count='H'
				previous_batch_count=previous_batch_count
			else:
				sc_row.day_count=previous_batch_count+1
				previous_batch_count=sc_row.day_count				
			
			sc_row.opening_qty=0
			sc_row.in_qty=flt(d.actual_qty, float_precision) if flt(d.actual_qty) > 0 else 0
			sc_row.out_qty=abs(flt(d.actual_qty, float_precision))	 if flt(d.actual_qty) < 0 else 0
			sc_row.bal_qty=sc_row.opening_qty+flt(d.actual_qty, float_precision)
			sc_row.rate=0
			sc_row.amount=0
			if sc_row.day_count!='H' and cint(sc_row.day_count)>=16 and cint(sc_row.day_count)<=25:
				sc_row.rate=storage_charges_16_25_days
				sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
			elif sc_row.day_count!='H' and cint(sc_row.day_count)>25:
				sc_row.rate=storage_charges_beyond_26_days
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
					if next_date in holiday_list_days and previous_batch_count <15:
						sc_row.day_count='H'
						previous_batch_count=previous_batch_count
					else:
						sc_row.day_count=previous_batch_count+1
						previous_batch_count=sc_row.day_count					
					sc_row.opening_qty=previous_opening_qty
					sc_row.in_qty=previous_in_qty
					sc_row.out_qty=previous_out_qty
					sc_row.bal_qty=previous_balance_qty
					sc_row.rate=0
					sc_row.amount=0
					if sc_row.day_count!='H' and cint(sc_row.day_count)>=16 and cint(sc_row.day_count)<=25:
						sc_row.rate=storage_charges_16_25_days
						sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
					elif sc_row.day_count!='H' and cint(sc_row.day_count)>25:
						sc_row.rate=storage_charges_beyond_26_days
						sc_row.amount=flt(sc_row.bal_qty*sc_row.rate)
					sc_data.append(sc_row)
					next_date=add_days(next_date,1)
		loop=loop+1

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
	query = frappe.db.sql(
		"""
			select 
				sle.vessel,
				sle.item_code,
				batch_package.batch_no,	
				case 
					when (sle.posting_time > '06:00:00'
					and sle.posting_time <= '24:00:00')
						then  date_add(sle.posting_date, INTERVAL +1 DAY) 
					else sle.posting_date
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
			where
				sle.docstatus < 2
				and sle.is_cancelled = 0
				and sle.has_batch_no = 1
				and actual_qty >0
			 {0}
			group by
				sle.vessel,
				sle.item_code,
				batch_package.batch_no,
				show_date
UNION 
			select 
				sle.vessel,
				sle.item_code,
				batch_package.batch_no,
				sle.posting_date as show_date,
				sum(batch_package.qty) as actual_qty,
				manufacturing_date
			from
				`tabStock Ledger Entry` sle
			inner join `tabSerial and Batch Entry` batch_package
			on
				sle.serial_and_batch_bundle = batch_package.parent
			inner join `tabBatch` batch 
			on batch_package.batch_no =batch.name 
			where
				sle.docstatus < 2
				and sle.is_cancelled = 0
				and sle.has_batch_no = 1
				and actual_qty <0
			{0}
			group by
				sle.vessel,
				sle.item_code,
				batch_package.batch_no,
				posting_date
order by vessel ,item_code ,manufacturing_date,show_date				
		
""".format(conditions),filters,as_dict=1,debug=1)	
	return query


def get_conditions(filters):
	conditions =""

	if filters.vessel:
		conditions += " and sle.vessel = %(vessel)s"


	first_line_ashore=frappe.db.get_value('Statement of Fact', filters.vessel, 'first_line_ashore')
	print(first_line_ashore,type(first_line_ashore))
	first_line_ashore=get_datetime(datetime_in_user_format(first_line_ashore))
	print(first_line_ashore,type(first_line_ashore))
	if not first_line_ashore:
		frappe.throw(_("First line ashore is required in SOF for the vessel"))



	if filters.get("from_date") and filters.get("to_date"):
		print(type(first_line_ashore),type(filters.get("to_date")))
		if get_datetime(filters.get("to_date")) < first_line_ashore:
			frappe.throw(_("To date {0} should be greater then first line ashore {1}".format(filters.get("to_date"),first_line_ashore)))
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