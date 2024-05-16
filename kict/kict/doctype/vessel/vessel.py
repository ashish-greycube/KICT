# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import _
from frappe.utils import flt
from frappe.utils import today


class Vessel(Document):
	
	def validate(self):
		self.validate_duplicate_entry_of_item()
		self.set_total_tonnage()
		self.set_unique_bl_no()
		self.set_customer_specific_grt()

	def set_customer_specific_grt(self):
		get_unique_customer = frappe.db.get_list("Vessel Details",parent_doctype="Vessel",filters={"parent":self.name},fields=['distinct customer_name'])
		print(get_unique_customer)
		print(self.name)
		final_customer_specific_grt = []
		for customer in get_unique_customer:
			customer_specific_total = 0
			for item in self.get("vessel_details"):
				if item.customer_name == customer.customer_name:
					if item.tonnage_mt:
						customer_specific_total = customer_specific_total + item.tonnage_mt
			customer_specific_grt = {}
			customer_specific_grt["customer"]=customer.customer_name
			customer_specific_grt["grt"]=customer_specific_total
			final_customer_specific_grt.append(customer_specific_grt)
		print(final_customer_specific_grt,"---------final_customer_specific_grt")
		for row in self.get("vessel_details"):
			for ele in final_customer_specific_grt:
				print(ele)
				print(ele.get("customer"))
				if row.customer_name == ele.get("customer"):
					row.customer_specific_grt = ele.get("grt")

	def set_total_tonnage(self):
		total_tonnage = 0
		for row in self.get("vessel_details"):
			if row.tonnage_mt:
				total_tonnage = total_tonnage + row.tonnage_mt

		self.total_tonnage_mt = total_tonnage

	def set_unique_bl_no(self):
		vessel_details = self.get("vessel_details")
		for row in vessel_details:
			if row.bl_order_ref_no:
				pass
			else:
				row.bl_order_ref_no = vessel_details[vessel_details.index(row)].name

	def validate_duplicate_entry_of_item(self):
		vessel_details = self.get("vessel_details")
		item_name = []
		for row in vessel_details:
			if row.item not in item_name:
				item_name.append(row.item)
			else :
				frappe.throw(_("Row #{0}: You cannot add {1} again.").format(row.idx,row.item))


@frappe.whitelist()
def get_all_unique_customer_from_vessel(docname):
	customer_list = frappe.db.get_all("Vessel Details", 
							 filters={"parent": docname}, 
							   fields=["distinct customer_name","customer_specific_grt"])
	return customer_list

@frappe.whitelist()
def create_sales_order_from_vessel(source_name, target_doc=None, hrs=None, qty=None, customer=None,doctype=None):
	def update_item(source, target,source_parent):
		pass
	
	def set_missing_values(source, target):

		bh_bill_to = frappe.db.get_value(doctype,source_name,"bh_bill_to")
		vessel_details_filter_for_cargo={"parent":source_name}
		if bh_bill_to=='Agent':
			pass
			
		elif bh_bill_to=='Customer':
			vessel_details_filter_for_cargo['customer_name']=customer
			price_list, currency = frappe.db.get_value(
			"Customer", {"name": customer}, ["default_price_list", "default_currency"]
		    )
			if price_list:
				target.selling_price_list = price_list
			if currency:
				target.currency = currency
		cargo_name = frappe.db.get_list("Vessel Details",parent_doctype="Vessel",filters=vessel_details_filter_for_cargo,fields=["distinct item"])

		target.customer=customer
		target.delivery_date = today()		

		vessel_type = frappe.db.get_value(doctype,source_name,"costal_foreign_vessle")
		if vessel_type == "Foreign":
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_foreign_vessel")
			item_code = item
		else :
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_coastal_vessel")
			item_code = item
		vessel_grt = frappe.db.get_value(doctype,source_name,"grt")

		all_cargo = ",".join((ele.item if ele.item!=None else '') for ele in cargo_name)
		if bh_bill_to=='Agent':
			vessel_grt = frappe.db.get_value(doctype,source_name,"grt")
			qty = vessel_grt * flt(hrs)
		else :
			customer_specific_grt = frappe.db.get_value("Vessel Details",{"parent":source_name,"customer_name":customer},["customer_specific_grt"])
			qty = customer_specific_grt * flt(hrs)

		target.append("items",{"item_code":item_code,"qty":qty})

	
	doc = get_mapped_doc('Vessel', source_name, {
		'Vessel': {
			'doctype': 'Sales Order',
			# 'field_map': {
			# 	'agent_name':'name',
			# },			
			'validation': {
				'docstatus': ['!=', 2]
			}
		},
		"Vessel Details": {
			"doctype": "Sales Order Item",
			"condition":lambda doc:len(frappe.db.get_list("Vessel Details",filters={"parent":source_name}))<0,
			# "postprocess":update_item
		},		
	}, target_doc,set_missing_values)
	doc.run_method("set_missing_values")
	doc.run_method("calculate_taxes_and_totals")
	doc.save()	

	return doc.name