# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import _
from frappe.utils import today


class Vessel(Document):
	
	def validate(self):
		self.set_total_tonnage()
		self.set_unique_bl_no()
		self.validate_duplicate_entry_of_item()

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
	print("get_all_unique_customer_from_vessel")
	customer_list = frappe.db.get_all("Vessel Details", 
							 filters={"parent": docname}, 
							   fields=["distinct customer_name"])
	return customer_list

@frappe.whitelist()
def create_sales_order_from_vessel(source_name, target_doc=None, hrs=None, customer=None,doctype=None):
	print(source_name,"--------------")
	def update_item(source, target,source_parent):
		pass
	
	def set_missing_values(source, target):
		print(source)
		print(target,"target----------")
		print(customer)
		target.customer=customer
		target.delivery_date = today()
		price_list, currency = frappe.db.get_value(
			"Customer", {"name": customer}, ["default_price_list", "default_currency"]
		)
		print(price_list,"price_list---------")
		if price_list:
			target.selling_price_list = price_list
		if currency:
			target.currency = currency		

		vessel_type = frappe.db.get_value(doctype,source_name,"costal_foreign_vessle")
		if vessel_type == "Foreign":
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_foreign_vessel")
			print(item,"birth_hire_item_for_foreign_vessel----------------")
			item_code = item
		else :
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_coastal_vessel")
			item_code = item
			print(item)
		vessel_grt = frappe.db.get_value(doctype,source_name,"grt")

		cargo_name = frappe.db.get_list("Vessel Details",parent_doctype="Vessel",filters={"parent":source_name},fields=["distinct item"])
		print(cargo_name)
		all_cargo = ",".join(ele.item for ele in cargo_name)
		print(all_cargo)

		print(hrs,"---hrs---",type(hrs))
		qty = vessel_grt * int(hrs)

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
	# print(doc.as_dict())
	doc.run_method("set_missing_values")
	doc.run_method("calculate_taxes_and_totals")
	doc.save()	
	print(target_doc)
	print(doc,"Doc")
	print(doc.name)

	return doc.name

	# print("make_perfoma_invoice")
	# so = frappe.new_doc("Sales Order")
	# so.customer = customer
	# so.delivery_date = today()
	# print(today())
	# row = so.append("items",{})
	# row.qty = qty
	# vessel_type = frappe.get_value(doctype,source_name,"costal_foreign_vessle")
	# print(vessel_type)
	# print(type(vessel_type))
	# if vessel_type == "Foreign":
	# 	item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_foreign_vessel")
	# 	print(item,"birth_hire_item_for_foreign_vessel----------------")
	# 	row.item_code = item
	# else :
	# 	item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_coastal_vessel")
	# 	row.item_code = item
	# 	print(item)
	
	# so.flags.ignore_permission
	# so.run_method("set_missing_values")
	# so.run_method("calculate_taxes_and_totals")

	# so.save()
	# print(so.name)
	# return so.name