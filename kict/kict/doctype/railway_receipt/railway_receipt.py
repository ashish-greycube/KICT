# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import _
from frappe.utils import get_link_to_form
  

class RailwayReceipt(Document):
	def before_insert(self):
		rcn_no = self.rcn_unique_no
		rake_dispatch_doc = frappe.get_doc("Rake Dispatch",rcn_no)
		for row in rake_dispatch_doc.get("plotwise_silo_qty_detail"):
			railway_receipt_item_row = self.append("railway_receipt_item_details",{})
			if row.customer_name:
				railway_receipt_item_row.customer_name = row.customer_name
			if row.vessel:
				railway_receipt_item_row.vessel = row.vessel
			if row.item:
				railway_receipt_item_row.item = row.item
			if row.commodity_grade:
				railway_receipt_item_row.grade = row.commodity_grade
			if row.coal_commodity:
				railway_receipt_item_row.coal_commodity = row.coal_commodity
			if row.plot:
				railway_receipt_item_row.plot = row.plot
			if row.silo_qty:
				railway_receipt_item_row.rr_item_weight_mt = row.silo_qty
			
			railway_receipt_item_row.is_billed = "No"
			railway_receipt_item_row.is_dn_created = "No"

	def validate(self):
		self.set_rr_weight()
	
	def set_rr_weight(self):
		railway_item_detail = self.get("railway_receipt_item_details")
		total_weight = 0
		if len(railway_item_detail) > 0:
			for row in self.get("railway_receipt_item_details"):
				if row.get("rr_item_weight_mt"):
					total_weight = total_weight + row.rr_item_weight_mt

		self.rr_weight = total_weight

	def on_submit(self):
		create_delivery_note_from_railway_receipt(self.name)
			
@frappe.whitelist()
def create_delivery_note_from_railway_receipt(docname):
	doc = frappe.get_doc("Railway Receipt",docname)
	railway_receipt_item = doc.get("railway_receipt_item_details")
	for row in railway_receipt_item:
		if row.is_dn_created != 'Yes':
			dn = frappe.new_doc("Delivery Note")
			dn.customer = row.customer_name
			dn.set_posting_time = 1
			dn.posting_date = doc.rr_date
			dn.custom_transports_mode = 'By Rake'
			dn.custom_rcn = doc.name
			dn.custom_railway_receipt_detail = row.name

			price_list, currency = frappe.db.get_value("Customer", {"name": row.customer_name}, ["default_price_list", "default_currency"])
			if price_list:
				dn.selling_price_list = price_list
			if currency:
				dn.currency = currency
			dn_item_row = dn.append("items",{})
			dn_item_row.item_code = row.item
			dn_item_row.qty = row.rr_item_weight_mt
			dn_item_row.vessel = row.vessel

			dn.run_method("set_missing_values")
			dn.run_method("calculate_taxes_and_totals")
			dn.save(ignore_permissions=True)
			dn.submit()

			row.is_dn_created = 'Yes'
			doc.save(ignore_permissions=True)
			frappe.msgprint(_('Delivery Note {0} is created').format(get_link_to_form("Delivery Note",dn.name)),alert=True)