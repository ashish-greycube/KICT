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
		get_unique_customer=[]
		for row in self.get("vessel_details"):
			if row.customer_name not in get_unique_customer:
				get_unique_customer.append({"customer_name":row.customer_name})
		final_customer_specific_grt = []
		for customer in get_unique_customer:
			customer_specific_total = 0
			for item in self.get("vessel_details"):
				if item.customer_name == customer.get("customer_name"):
					if item.tonnage_mt:
						customer_specific_total = customer_specific_total + item.tonnage_mt
			customer_specific_grt = {}
			customer_specific_grt["customer"]=customer.get("customer_name")
			customer_specific_grt["grt"]=(customer_specific_total/self.total_tonnage_mt)*100
			final_customer_specific_grt.append(customer_specific_grt)
		for row in self.get("vessel_details"):
			for ele in final_customer_specific_grt:
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
def get_unique_customer_and_customer_specific_grt_from_vessel(docname):
	customer_list = frappe.db.get_all("Vessel Details", 
							parent_doctype='Vessel',
							filters={"parent": docname}, 
							fields=["distinct customer_name","customer_specific_grt"])
	return customer_list



@frappe.whitelist()
def create_sales_order_from_vessel_for_berth_charges(source_name, target_doc=None, qty=None, customer=None,is_single_customer=None,
													 customer_specific_grt_percentage=None,customer_specific_grt_field=None,bill_hours=None,doctype=None):
	# def update_item(source, target,source_parent):
	# 	pass
	
	def set_missing_values(source, target):
		bh_bill_to = frappe.db.get_value(doctype,source_name,"bh_bill_to")
		vessel_details_filter_for_cargo={"parent":source_name}
		total_tonnage_mt=frappe.db.get_value(doctype,source_name,"total_tonnage_mt")

		if bh_bill_to=='Agent':
			custom_quantity_in_mt=total_tonnage_mt
			
		elif bh_bill_to=='Customer':
			if is_single_customer=='true':
				custom_quantity_in_mt=total_tonnage_mt
			elif is_single_customer=='false':
				custom_quantity_in_mt=(flt(customer_specific_grt_percentage)*total_tonnage_mt)/100
			vessel_details_filter_for_cargo['customer_name']=customer

			price_list, currency = frappe.db.get_value(
			"Customer", {"name": customer}, ["default_price_list", "default_currency"]
		    )
			if price_list:
				target.selling_price_list = price_list
			if currency:
				target.currency = currency

		cargo_name = frappe.db.get_list("Vessel Details",parent_doctype="Vessel",filters=vessel_details_filter_for_cargo,fields=["distinct item"])
		all_cargo = ",".join((ele.item if ele.item!=None else '') for ele in cargo_name)
		target.custom_cargo_item=all_cargo
		target.custom_quantity_in_mt=custom_quantity_in_mt
		target.custom_type_of_invoice="Berth Hire Charges"
		target.customer=customer
		target.delivery_date = today()		
		target.vessel=source_name

		vessel_type = frappe.db.get_value(doctype,source_name,"costal_foreign_vessle")
		if vessel_type == "Foreign":
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_foreign_vessel")
			item_code = item
		else :
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_coastal_vessel")
			item_code = item

		target.append("items",{"item_code":item_code,"qty":qty,"custom_grt":customer_specific_grt_field,"custom_expected_hours_of_stay":bill_hours})
	
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

@frappe.whitelist()
def get_berth_stay_hours(vessel):
	berth_stay_hours=0
	statement_of_fact_list = frappe.db.get_all("Statement of Fact", 
							filters={"vessel": vessel}, 
							fields=["all_line_cast_off","first_line_ashore"])
	if len(statement_of_fact_list)>0:
		all_line_cast_off=statement_of_fact_list[0].all_line_cast_off
		first_line_ashore=statement_of_fact_list[0].first_line_ashore
		berth_stay_hours=frappe.utils.time_diff_in_hours(all_line_cast_off,first_line_ashore)

	return berth_stay_hours


@frappe.whitelist()
def create_sales_invoice_from_vessel_for_berth_charges(source_name, target_doc=None, qty=None, customer=None,is_single_customer=None,
														customer_specific_grt_percentage=None,customer_specific_grt_field=None,bill_hours=None,doctype=None):
	# def update_item(source, target,source_parent):
	# 	pass
	
	def set_missing_values(source, target):
		bh_bill_to = frappe.db.get_value(doctype,source_name,"bh_bill_to")
		vessel_details_filter_for_cargo={"parent":source_name}
		total_tonnage_mt=frappe.db.get_value(doctype,source_name,"total_tonnage_mt")

		if bh_bill_to=='Agent':
			custom_quantity_in_mt=total_tonnage_mt
			
		elif bh_bill_to=='Customer':
			if is_single_customer=='true':
				custom_quantity_in_mt=total_tonnage_mt
			elif is_single_customer=='false':
				custom_quantity_in_mt=(flt(customer_specific_grt_percentage)*total_tonnage_mt)/100
			vessel_details_filter_for_cargo['customer_name']=customer

			price_list, currency = frappe.db.get_value(
			"Customer", {"name": customer}, ["default_price_list", "default_currency"]
		    )
			if price_list:
				target.selling_price_list = price_list
			if currency:
				target.currency = currency

		cargo_name = frappe.db.get_list("Vessel Details",parent_doctype="Vessel",filters=vessel_details_filter_for_cargo,fields=["distinct item"])
		all_cargo = ",".join((ele.item if ele.item!=None else '') for ele in cargo_name)
		target.custom_cargo_item=all_cargo
		target.custom_quantity_in_mt=custom_quantity_in_mt
		target.custom_type_of_invoice="Berth Hire Charges"
		target.customer=customer
		target.due_date = today()		
		target.vessel=source_name

		vessel_type = frappe.db.get_value(doctype,source_name,"costal_foreign_vessle")
		if vessel_type == "Foreign":
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_foreign_vessel")
			item_code = item
		else :
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_coastal_vessel")
			item_code = item

		target.append("items",{"item_code":item_code,"qty":qty,"custom_grt":customer_specific_grt_field,"custom_expected_hours_of_stay":bill_hours})
	
	doc = get_mapped_doc('Vessel', source_name, {
		'Vessel': {
			'doctype': 'Sales Invoice',
			# 'field_map': {
			# 	'agent_name':'name',
			# },			
			'validation': {
				'docstatus': ['!=', 2]
			}
		},
		"Vessel Details": {
			"doctype": "Sales Invoice Item",
			"condition":lambda doc:len(frappe.db.get_list("Vessel Details",filters={"parent":source_name}))<0,
			# "postprocess":update_item
		},		
	}, target_doc,set_missing_values)
	doc.run_method("set_missing_values")
	doc.run_method("calculate_taxes_and_totals")
	doc.save()	
	return doc.name

@frappe.whitelist()
def get_unique_item_and_customer_from_vessel(docname):
    item_list = frappe.db.get_list("Vessel Details",
                                parent_doctype="Vessel",
                                filters={"parent":docname},
                                fields=["item","customer_name","name","tonnage_mt"])
    return item_list

@frappe.whitelist()
def create_sales_invoice_for_cargo_handling_charges_from_vessel(source_name, target_doc=None,cargo_item_field=None,type_of_invoice=None,vessel_details_hex_code_field=None,customer_name_field=None,total_tonnage_field=None,doctype=None):
	# def update_item(source, target,source_parent):
	# 	pass
	def set_missing_values(source, target):
	
		price_list, currency = frappe.db.get_value("Customer", {"name": customer_name_field}, ["default_price_list", "default_currency"])
		if price_list:
			target.selling_price_list = price_list
		if currency:
			target.currency = currency

		# cargo_name = frappe.db.get_list("Vessel Details",parent_doctype="Vessel",filters=vessel_details_filter_for_cargo,fields=["distinct item"])
		# all_cargo = ",".join((ele.item if ele.item!=None else '') for ele in cargo_name)
		# target.custom_cargo_item=all_cargo
		# target.custom_quantity_in_mt=custom_quantity_in_mt

		# target.type_of_invoice=type_of_invoice
		target.custom_type_of_invoice="Cargo Handling Charges"
		target.customer=customer_name_field
		target.due_date = today()		
		target.vessel=source_name
		item_code = frappe.db.get_single_value("Coal Settings","ch_charges")

		# nothing on vessel type

		item_row=target.append("items",{"item_code":item_code,"qty":total_tonnage_field,"description":cargo_item_field,"vessel_detail":vessel_details_hex_code_field})

		
		
	
	doc = get_mapped_doc('Vessel', source_name, {
		'Vessel': {
			'doctype': 'Sales Invoice',
			# 'field_map': {
			# 	'agent_name':'name',
			# },			
			'validation': {
				'docstatus': ['!=', 2]
			}
		},
		"Vessel Details": {
			"doctype": "Sales Invoice Item",
			"condition":lambda doc:len(frappe.db.get_list("Vessel Details",filters={"parent":source_name}))<0,
			# "postprocess":update_item
		},		
	}, target_doc,set_missing_values)
	doc.run_method("set_missing_values")
	doc.run_method("calculate_taxes_and_totals")
	doc.save()	
	return doc.name