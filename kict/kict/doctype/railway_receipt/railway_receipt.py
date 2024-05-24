# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
  

class RailwayReceipt(Document):
	def before_insert(self):
		rcn_no = self.rcn_unique_no
		print(rcn_no)
		pass

@frappe.whitelist()
def create_delivery_note_from_railway_receipt(source_name,target_doc=None,doctype=None):
	
	def set_missing_values(source, target):
		# pendind
		rr_weight = frappe.db.get_value(doctype,source_name,"rr_weight")
		rr_date = frappe.db.get_value(doctype,source_name,"rr_date")
		customer = 'TATA STEEL LIMITED-TSL'
		# mandatory to check set_posting_time checkbox to edit posting date
		target.set_posting_time = 1
		target.customer=customer
		target.posting_date = rr_date

		price_list, currency = frappe.db.get_value("Customer", {"name": customer}, ["default_price_list", "default_currency"])
		if price_list:
			target.selling_price_list = price_list
		if currency:
			target.currency = currency
		target.custom_transports_mode='By Rake'
		target.append("items",{"item_code":"Coking Coal-TSL","qty":rr_weight,"vessel":"new16052024"})

	doc = get_mapped_doc('Railway Receipt', source_name, {
		'Railway Receipt': {
			'doctype': 'Delivery Note',
			'field_map': {
				'name':'custom_rcn'
			},			
			'validation': {
				'docstatus': ['!=', 2]
			}
		}		
	}, target_doc,set_missing_values)
	doc.run_method("set_missing_values")
	doc.run_method("calculate_taxes_and_totals")
	doc.save()	
	return doc.name