# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import _
from frappe.utils import get_link_to_form,today,nowtime,flt,cstr,get_timestamp,getdate,get_time,cint
from frappe.query_builder.functions import CombineDatetime, Sum  
from erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle	import get_qty_based_available_batches
import json

class RailwayReceipt(Document):
	def before_insert(self):
		donot_set_rr_weight_from_silo_weight_in_rr = frappe.db.get_single_value('Coal Settings', 'donot_set_rr_weight_from_silo_weight_in_rr')
		if donot_set_rr_weight_from_silo_weight_in_rr==0:
			rcn_no = self.rcn_unique_no
			rake_dispatch_doc = frappe.get_doc("Rake Dispatch",rcn_no)
			self.railway_receipt_item_details=[]
			for row in rake_dispatch_doc.get("rake_prelim_entry"):
				railway_receipt_item_row = self.append("railway_receipt_item_details",{})
				if row.customer_name:
					railway_receipt_item_row.customer_name = row.customer_name
				if row.vcn_no:
					railway_receipt_item_row.vessel = row.vcn_no
				if row.item:
					railway_receipt_item_row.item = row.item
				if row.grade:
					railway_receipt_item_row.grade = row.grade
				if row.coal_commodity:
					railway_receipt_item_row.coal_commodity = row.coal_commodity
				if row.silo_loading_weight:
					railway_receipt_item_row.rr_item_weight_mt = row.silo_loading_weight
				if row.commercial_destination_customer:
					railway_receipt_item_row.commercial_destination_customer = row.commercial_destination_customer
				if row.commercial_destination_item:
					railway_receipt_item_row.commercial_destination_item = row.commercial_destination_item
				
				railway_receipt_item_row.is_billed = "No"
				railway_receipt_item_row.is_dn_created = "No"

	def validate(self):
		self.set_rr_weight()
		self.set_item_cw_and_pcc()
		self.claculate_total_punitive_amount()
	
	def set_rr_weight(self):
		railway_item_detail = self.get("railway_receipt_item_details")
		total_weight = 0
		if len(railway_item_detail) > 0:
			for row in self.get("railway_receipt_item_details"):
				if row.get("rr_item_weight_mt"):
					total_weight = total_weight + row.rr_item_weight_mt

		self.rr_weight = total_weight
	
	def set_item_cw_and_pcc(self):
		railway_receipt_item = self.get("railway_receipt_item_details")
		for row in railway_receipt_item:
			if self.chargable_weight == 0 or self.chargable_weight == None :
				frappe.throw(_("Please set chargable weight"))
			elif self.permisible_carrying_capacity == 0 or self.permisible_carrying_capacity == None:
				frappe.throw(_("Please set permisible carrying capacity"))
			if row.rr_item_weight_mt and self.rr_weight and self.chargable_weight:
				item_cw = (row.rr_item_weight_mt / self.rr_weight) * self.chargable_weight
			if row.rr_item_weight_mt and self.rr_weight and self.permisible_carrying_capacity:
				item_pcc = (row.rr_item_weight_mt / self.rr_weight) * self.permisible_carrying_capacity
			
			row.item_cw = item_cw or 0
			row.item_pcc = item_pcc or 0

	def claculate_total_punitive_amount(self):
		total_punitive_amount = (self.pol1 or 0) + (self.pol2 or 0)
		self.total_punitive_amount = total_punitive_amount

	def on_submit(self):
		create_delivery_note_from_railway_receipt(self.name)

@frappe.whitelist()
def create_delivery_note_from_railway_receipt(docname):
	float_precision = cint(frappe.db.get_default("float_precision")) or 3
	def dn_append_child_item_based_on_batchs(dn,item_code,qty,vessel,batch_no,warehouse):
		# add row in dn child table
		dn_item_row = dn.append("items",{})
		dn_item_row.item_code =item_code
		dn_item_row.qty = qty
		dn_item_row.vessel = vessel
		dn_item_row.batch_no = batch_no
		dn_item_row.warehouse = warehouse
		dn_item_row.use_serial_batch_fields=1
		return dn
	
	doc = frappe.get_doc("Railway Receipt",docname)
	release_detail=frappe.db.get_value('Rake Dispatch', docname, 'release_time')
	if release_detail:
		release_date=getdate(release_detail)
		release_time=get_time(release_detail)
	else:
		frappe.throw(_("Please set release time in rake dispatch {0}".format(docname)))		
	
	railway_receipt_item = doc.get("railway_receipt_item_details")
	for row in railway_receipt_item:
		# row.rr_item_weight_mt=flt((row.rr_item_weight_mt),float_precision)
		if row.is_dn_created != 'Yes':
			dn = frappe.new_doc("Delivery Note")
			dn.customer = row.commercial_destination_customer
			dn.set_posting_time = 1
			dn.posting_date = release_date
			dn.posting_time=release_time 
			dn.custom_transports_mode = 'By Rake'
			dn.custom_rcn = doc.name
			dn.vessel = row.vessel
			dn.custom_railway_receipt_detail = row.name
			dn.custom_rake_no = frappe.db.get_value("Rake Dispatch",docname,"rake_no")
			price_list, currency = frappe.db.get_value("Customer", {"name": row.commercial_destination_customer}, ["default_price_list", "default_currency"])
			if price_list:
				dn.selling_price_list = price_list
			if currency:
				dn.currency = currency

			#  fetch batches
			args=frappe._dict({'item_code': row.item, 
		 	'has_serial_no': '0', 
			'has_batch_no': '1', 
			'qty':row.rr_item_weight_mt, 
			'based_on': 'FIFO', 
			'vessel':row.vessel,
			'posting_date': release_date or None,
			'posting_time': release_time or None,
			'cmd': "kict.kict.doctype.railway_receipt.railway_receipt.get_auto_data"
			})
			print('='*10)
			print('args',args)
			available_batches=get_available_batches(args)
			print('available_batches=============',available_batches)
			# check if batch total qty is less than required qty
			
			qty_from_batches=0
			for batch in available_batches:
				qty_from_batches=flt((qty_from_batches+batch.qty),float_precision)
			if len(available_batches) < 1:
				table_html = frappe.bold("No batches found.")
				msg="The qty available from batches is {0}, whereas required qty is {1}. Hence cannot proceed.".format(frappe.bold(qty_from_batches),frappe.bold(row.rr_item_weight_mt))	
				frappe.throw(_(table_html+"<br>"+msg))				
			if row.rr_item_weight_mt>qty_from_batches:
				table_body="<table border='1'><tr><td><b>Batch</b></td><td><b>Warehouse</b></td><td><b>Qty</b></td></tr>"
				table_row=""
				for item in available_batches:
					table_row=table_row+"<tr><td>"+item.batch_no+"</td><td>"+item.warehouse+"</td><td>"+cstr(item.qty)+"</td></tr>"
				table_html=table_body+table_row+"</table>"			
				msg="The qty available from batches is {0}, whereas required qty is {1}. Hence cannot proceed.".format(frappe.bold(qty_from_batches),frappe.bold(row.rr_item_weight_mt))	
				frappe.throw(_(table_html+"<br>"+msg))
			
			# for each batch, warehouse add seperate line item
			for batch in available_batches:
				dn_append_child_item_based_on_batchs(dn,row.item,batch.qty,row.vessel,batch.batch_no,batch.warehouse)
			
			dn.run_method("set_missing_values")
			dn.run_method("calculate_taxes_and_totals")
			# print('dn',(dn.as_dict()).get("items"))
			# x=(dn.as_dict()).get("items")
			# for i in x:
			# 	print(i.item_code,i.qty,i.warehouse,i.batch_no)
			# frappe.throw(_("no"))
			dn.save(ignore_permissions=True)
			dn.submit()
			row.is_dn_created = 'Yes'
			doc.save(ignore_permissions=True)
			print('delivery note info====')
			print(dn.name,dn.posting_date,dn.posting_time)
			frappe.db.commit()
			frappe.msgprint(_('Delivery Note {0} is created').format(get_link_to_form("Delivery Note",dn.name)),alert=True)




# copied from erpnext/erpnext/stock/doctype/serial_and_batch_bundle/serial_and_batch_bundle.get_available_batches
# filter based on vessel
def get_available_batches(kwargs):
	print('kwargs--custom',kwargs)
	stock_ledger_entry = frappe.qb.DocType("Stock Ledger Entry")
	batch_ledger = frappe.qb.DocType("Serial and Batch Entry")
	batch_table = frappe.qb.DocType("Batch")
	qty = flt(kwargs.qty)
	query = (
		frappe.qb.from_(stock_ledger_entry)
		.inner_join(batch_ledger)
		.on(stock_ledger_entry.serial_and_batch_bundle == batch_ledger.parent)
		.inner_join(batch_table)
		.on(batch_ledger.batch_no == batch_table.name)
		.select(
			batch_ledger.batch_no,
			batch_ledger.warehouse,
			Sum(batch_ledger.qty).as_("qty"),
		)
		.where(
			(batch_table.disabled == 0)
			& ((batch_table.expiry_date >= today()) | (batch_table.expiry_date.isnull()))
		)
		.where(stock_ledger_entry.is_cancelled == 0)
		.groupby(batch_ledger.batch_no, batch_ledger.warehouse)
	)
	# change in original function
	if kwargs.get("vessel"):
		query = query.where(stock_ledger_entry.vessel == kwargs.vessel)

	if kwargs.get("posting_date"):
		if kwargs.get("posting_time") is None:
			kwargs.posting_time = nowtime()

		timestamp_condition = CombineDatetime(
			stock_ledger_entry.posting_date, stock_ledger_entry.posting_time
		) <= CombineDatetime(kwargs.posting_date, kwargs.posting_time)
		print('timestamp_condition',timestamp_condition)
		query = query.where(timestamp_condition)

	for field in ["warehouse", "item_code"]:
		if not kwargs.get(field):
			continue

		if isinstance(kwargs.get(field), list):
			query = query.where(stock_ledger_entry[field].isin(kwargs.get(field)))
		else:
			query = query.where(stock_ledger_entry[field] == kwargs.get(field))

	if kwargs.get("batch_no"):
		if isinstance(kwargs.batch_no, list):
			query = query.where(batch_ledger.batch_no.isin(kwargs.batch_no))
		else:
			query = query.where(batch_ledger.batch_no == kwargs.batch_no)

	if kwargs.based_on == "LIFO":
		query = query.orderby(batch_table.creation, order=frappe.qb.desc)
	elif kwargs.based_on == "Expiry":
		query = query.orderby(batch_table.expiry_date)
	else:
		query = query.orderby(batch_table.manufacturing_date)

	if kwargs.get("ignore_voucher_nos"):
		query = query.where(stock_ledger_entry.voucher_no.notin(kwargs.get("ignore_voucher_nos")))

	data = query.run(as_dict=True,debug=1)
	print('data1',data)

	# change in original function
	if not kwargs.consider_negative_batches:
		data = list(filter(lambda x: x.qty > 0, data))

	if not qty:
		return data
	print('data2',data)
	
	print(get_qty_based_available_batches(data, qty),"get_qty_based_available_batches(data, qty)")	
	return get_qty_based_available_batches(data, qty)
	
@frappe.whitelist()
def submit_bulk_railway_receipts(rr_list=None):
	rr_list=frappe.db.get_all('Railway Receipt', filters={'docstatus': 0},pluck='name')
	# for rr in rr_list:
	# 	docstatus = frappe.db.get_value('Railway Receipt',rr, 'docstatus')
	# 	if docstatus!=0:
	# 		frappe.throw(_("You cannot select sbumitted railway receipt {0}".format(frappe.bold(rr))))
	rr_ordered_list=frappe.db.get_all('Rake Dispatch', filters={'name': ['in', rr_list]},order_by='release_time asc',)	
	submitted_rr=[]
	for rr in rr_ordered_list:
		doc = frappe.get_doc('Railway Receipt', rr)
		doc.submit()
		frappe.db.commit()
		submitted_rr.append(doc.name)
	submitted_rr=" ,".join(submitted_rr)
	frappe.msgprint(_("Railway Receipts {0} are submitted".format(frappe.bold(submitted_rr))))

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_unique_customer_item_list(doctype, txt, searchfield, start, page_len, filters):
	vcn_no = filters.get("vessel_name")
	return frappe.get_all(
		"Vessel Details",
		parent_doctype="Vessel",
		filters={"parent": vcn_no},
		fields=["distinct item"],
		as_list=1,
	)