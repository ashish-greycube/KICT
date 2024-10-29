# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import _
from frappe.utils import flt,cstr,today,cint
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.stock.get_item_details import get_price_list_rate_for


class Vessel(Document):
	def validate(self):
		self.validate_duplicate_entry_of_item()
		self.set_total_tonnage()
		self.set_unique_bl_no()
		self.set_customer_specific_grt()
		self.set_percent_berth_hire_si_in_vessel()
		self.set_percent_berth_hire_pi_in_vessel()
		self.set_cargo_closer_when_vessel_is_closed()

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

	def set_percent_berth_hire_si_in_vessel(self):
		total_billed_grt_for_si = 0
		for item in self.vessel_details:
			if item.grt_billed_for_bh_for_si:
				total_billed_grt_for_si = total_billed_grt_for_si + item.grt_billed_for_bh_for_si
		
		self.percent_berth_hire_si = (total_billed_grt_for_si * 100) / self.total_tonnage_mt

	def set_percent_berth_hire_pi_in_vessel(self):
		total_billed_grt_for_pi = 0
		for item in self.vessel_details:
			if item.grt_billed_for_bh_for_pi:
				total_billed_grt_for_pi = total_billed_grt_for_pi + item.grt_billed_for_bh_for_pi
		
		self.percent_berth_hire_pi = (total_billed_grt_for_pi * 100) / self.total_tonnage_mt

	def set_cargo_closer_when_vessel_is_closed(self):
		if self.vessel_closure==1:
			for row in self.get("vessel_details"):

				from erpnext.stock.report.stock_balance.stock_balance import execute
				company_name=frappe.get_value("Vessel",self.name,"company")
				first_line_ashore = frappe.db.get_value('Statement of Fact', self.name, 'first_line_ashore')
				filter_for_lv =frappe._dict({"company":company_name,"from_date":first_line_ashore,"to_date":today(),"item_code":row.item,"valuation_field_type":"Currency","vessel":[self.name]})
				data = execute(filter_for_lv)
				total_bal_val = 0
				for record in data[1]:
					total_bal_val = total_bal_val + record.bal_qty

				if(total_bal_val>0):
					frappe.throw(_("Row {0}: {1} stock is remaining {2}.<br>  You cannot close vessel.").format(row.idx,row.item,total_bal_val))

			for row in self.vessel_details:
				row.cargo_closure = 1
			frappe.msgprint(_("Cargo closure is set for all vessel items."),alert=True)

@frappe.whitelist()
def get_unique_customer_and_customer_specific_grt_from_vessel(docname):
	customer_list_with_po=[]
	
	customer_list = frappe.db.get_all("Vessel Details", 
							parent_doctype='Vessel',
							filters={"parent": docname}, 
							fields=["distinct customer_name","customer_specific_grt"])
	
	for customer in customer_list:
		final_po_no=''
		customer_po_no_list=frappe.db.get_all("Vessel Details", 
							parent_doctype='Vessel',
							filters={"parent": docname,"customer_name":customer.customer_name}, 
							fields=["customer_po_no"],order_by="idx")
		for po_no in customer_po_no_list:
			if po_no.get("customer_po_no")!="":
				final_po_no=po_no.get("customer_po_no")
				break
		customer['customer_po_no']=final_po_no

		customer_list_with_po.append(customer)
	
	return customer_list_with_po



@frappe.whitelist()
def create_sales_order_from_vessel_for_berth_charges(source_name, target_doc=None, qty=None, customer=None,is_single_customer=None,
													 customer_specific_grt_percentage=None,customer_specific_grt_field=None,customer_po_no_field=None,
													 bill_hours=None,proportionate_berth_hours_field=None,doctype=None):
	# def update_item(source, target,source_parent):
	# 	pass
	
	def set_missing_values(source, target):
		bh_bill_to = frappe.db.get_value(doctype,source_name,"bh_bill_to")
		vessel_details_filter_for_cargo={"parent":source_name}
		total_tonnage_mt=frappe.db.get_value(doctype,source_name,"total_tonnage_mt")

		if (bh_bill_to=='Agent' or  bh_bill_to=='OPA'):
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
		target.po_no = customer_po_no_field

		vessel_type = frappe.db.get_value(doctype,source_name,"costal_foreign_vessle")
		if vessel_type == "Foreign":
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_foreign_vessel")
			item_code = item
		else :
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_coastal_vessel")
			item_code = item

		target.append("items",{"item_code":item_code,"qty":qty,"custom_grt":customer_specific_grt_field,"custom_expected_hours_of_stay":bill_hours,"custom_proportionate_berth_hours":proportionate_berth_hours_field})
	
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
			"condition":lambda doc:len(doc.name)<0,
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
							fields=["vessel_stay_hours"])
	if len(statement_of_fact_list)>0:
		berth_stay_hours=statement_of_fact_list[0].vessel_stay_hours

	return berth_stay_hours


@frappe.whitelist()
def create_sales_invoice_from_vessel_for_berth_charges(source_name, target_doc=None, qty=None, customer=None,is_single_customer=None,
														customer_specific_grt_percentage=None,customer_specific_grt_field=None,customer_po_no_field=None,
														bill_hours=None,proportionate_berth_hours_field=None,doctype=None):
	# def update_item(source, target,source_parent):
	# 	pass
	
	def set_missing_values(source, target):
		bh_bill_to = frappe.db.get_value(doctype,source_name,"bh_bill_to")
		vessel_details_filter_for_cargo={"parent":source_name}
		total_tonnage_mt=frappe.db.get_value(doctype,source_name,"total_tonnage_mt")

		if (bh_bill_to=='Agent' or bh_bill_to=='OPA'):
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
		target.custom_cargo_item= all_cargo[:139] if len(all_cargo) > 139 else all_cargo
		target.custom_quantity_in_mt=custom_quantity_in_mt
		target.custom_type_of_invoice="Berth Hire Charges"
		target.customer=customer
		target.due_date = today()		
		target.vessel=source_name
		target.po_no = customer_po_no_field

		vessel_type = frappe.db.get_value(doctype,source_name,"costal_foreign_vessle")
		if vessel_type == "Foreign":
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_foreign_vessel")
			item_code = item
		else :
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_coastal_vessel")
			item_code = item

		vessel_first_line_ashore = cstr(frappe.format(frappe.db.get_value("Statement of Fact",source_name,"first_line_ashore"),"Datetime"))
		vessel_all_line_cast_off = cstr(frappe.format(frappe.db.get_value("Statement of Fact",source_name,"all_line_cast_off"),"Datetime"))
		vessel_total_stay_hours = cstr(frappe.db.get_value("Statement of Fact",source_name,"vessel_stay_hours"),"Datetime")
		print(vessel_total_stay_hours,"total hours")
		description = item_code + "<br> First Line Ashore : " + vessel_first_line_ashore + "<br> All Line Cast Off : " + vessel_all_line_cast_off + "<br> Total Hours : " + vessel_total_stay_hours
		print(description,"description---------------------------")
		target.append("items",{"item_code":item_code,"qty":qty,"custom_grt":customer_specific_grt_field,"custom_actual_hours_of_stay":bill_hours,"custom_proportionate_berth_hours":proportionate_berth_hours_field,"description":description})
	
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
			"condition":lambda doc:len(doc.name)<0,
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
								fields=["item","customer_name","name","tonnage_mt","customer_po_no"])
	return item_list

@frappe.whitelist()
def create_sales_invoice_for_cargo_handling_charges_from_vessel(source_name, target_doc=None,cargo_item_field=None,customer_name_field=None,type_of_billing_field=None,is_periodic_or_dispatch_field=None,rate_field=None,periodic_cargo_qty=None,non_periodic_cargo_qty=None,customer_po_no_field=None,from_date_field=None,to_date_field=None,doctype=None):
	# def update_item(source, target,source_parent):
	# 	pass
	def set_missing_values(source, target):
	
		price_list, currency = frappe.db.get_value("Customer", {"name": customer_name_field}, ["default_price_list", "default_currency"])
		if price_list:
			target.selling_price_list = price_list
		if currency:
			target.currency = currency

		target.custom_cargo_item = cargo_item_field
		target.custom_quantity_in_mt = flt(non_periodic_cargo_qty)

		# target.type_of_invoice=type_of_invoice
		target.custom_type_of_cargo_handling_invoice=is_periodic_or_dispatch_field
		target.custom_cargo_sub_type_of_invoice = type_of_billing_field

		target.custom_type_of_invoice="Cargo Handling Charges"
		if is_periodic_or_dispatch_field=="Periodic":
			target.custom_cargo_from_date = from_date_field
			target.custom_cargo_to_date = to_date_field
			print(type_of_billing_field,"-----------type_of_billing_field")
		target.customer=customer_name_field
		target.due_date = today()		
		target.vessel=source_name
		target.po_no = customer_po_no_field
		item_code = frappe.db.get_single_value("Coal Settings","ch_charges")

		# nothing on vessel type
		if is_periodic_or_dispatch_field in ["Non-Periodic","Dispatch"]:
			item_row=target.append("items",{"item_code":item_code,"qty":flt(non_periodic_cargo_qty),"description":cargo_item_field,"rate":rate_field})
		elif is_periodic_or_dispatch_field=="Periodic":
			item_row=target.append("items",{"item_code":item_code,"qty":flt(periodic_cargo_qty),"description":cargo_item_field,"rate":rate_field})
	
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
			"condition":lambda doc:len(doc.name)<0,
			# "postprocess":update_item
		},		
	}, target_doc,set_missing_values)
	doc.run_method("set_missing_values")
	doc.run_method("calculate_taxes_and_totals")
	doc.save()

	if is_periodic_or_dispatch_field=='Periodic':
		rr_details = get_qty_for_dispatch_periodic_type(source_name,cargo_item_field,from_date_field,to_date_field)
		participating_rr_details = rr_details[2]
		for ele in participating_rr_details:
			frappe.db.set_value("Railway Receipt Item Details",ele.name,"is_billed","Yes")
			frappe.db.set_value("Railway Receipt Item Details",ele.name,"sales_invoice_reference",doc.name)
	return doc.name

@frappe.whitelist()
def create_sales_invoice_for_storage_charges_from_vessel(source_name, target_doc=None,cargo_item_field=None,customer_name_field=None,total_tonnage_field=None,customer_po_no_field=None,doctype=None):

	from erpnext.stock.report.stock_balance.stock_balance import execute
	
	company_name=frappe.get_value(doctype,source_name,"company")
	first_line_ashore = frappe.db.get_value('Statement of Fact', source_name, 'first_line_ashore')
	filter_for_lv =frappe._dict({"company":company_name,"from_date":first_line_ashore,"to_date":today(),
							  "item_code":cargo_item_field,"valuation_field_type":"Currency","vessel":[source_name],"include_zero_stock_items":1})
	# sle_count=frappe.db.count('Stock Ledger Entry',filters={
	# 	'item_code':cargo_item_field,
    #      'posting_date':['between', [first_line_ashore, today()]],
    #      'vessel':source_name,
    #      'company':company_name})
	# if sle_count==0:
	# 	frappe.throw(_("1There is no stock entry for {0}. <br> You can not create tax invoice of storage charges.").format(cargo_item_field))
	data = execute(filter_for_lv)
	print('++'*10)
	print(filter_for_lv)
	print(data)
	print(data[1])
	if len(data[1])==0:
		frappe.throw(_("There is no stock entry for {0}. <br> You can not create tax invoice of storage charges.").format(cargo_item_field))
	else:
		total_bal_val = 0
		for record in data[1]:
			total_bal_val = total_bal_val + record.bal_qty

		if(total_bal_val>0):
			frappe.throw(_("{0} stock is remaining {1}.<br>  You can not create tax invoice of storage charges.").format(cargo_item_field,total_bal_val))
		else :
			# def update_item(source, target,source_parent):
			# 	pass

			def set_missing_values(source, target):
			
				price_list, currency = frappe.db.get_value("Customer", {"name": customer_name_field}, ["default_price_list", "default_currency"])
				if price_list:
					target.selling_price_list = price_list
				if currency:
					target.currency = currency

				target.custom_type_of_invoice="Storage Charges"
				target.customer=customer_name_field
				target.due_date = today()
				target.custom_cargo_item = cargo_item_field
				target.custom_quantity_in_mt = total_tonnage_field		
				target.vessel=source_name
				target.po_no = customer_po_no_field
				# item_code = frappe.db.get_single_value("Coal Settings","storage_charges_fixed")

				storage_charges_type = frappe.db.get_value("Customer",customer_name_field,"custom_storage_charge_based_on")
				if storage_charges_type == "Fixed Days":
					storage_charges_item_fixed = frappe.db.get_single_value("Coal Settings","storage_charges_fixed")
					handling_qty = get_qty_for_handling_loss_and_audit_shortage(source_name,cargo_item_field)
					storage_charges_qty = flt(total_tonnage_field)
					fixed_number_of_days = frappe.db.get_value("Customer",customer_name_field,"custom_no_of_days")
					description = "Storage Charges for "+cstr(fixed_number_of_days)+" days"
					item_row=target.append("items",{"item_code":storage_charges_item_fixed,"qty":storage_charges_qty,"description":description})
				if storage_charges_type == "Actual Storage Days":
					customer_doc=frappe.get_doc('Customer',customer_name_field)

					storage_charges_item_16_25 = customer_doc.custom_chargeable_storage_charges_slots_details[0].item
					storage_charges_item_beyond_26 = customer_doc.custom_chargeable_storage_charges_slots_details[1].item
					charges_for_16_25, charges_for_beyond_26, qty_for_16_25, qty_for_beyond_26 = get_rate_and_qty_for_actual_storage_type_based_on_storage_report(source_name,customer_name_field)
					print(charges_for_16_25, charges_for_beyond_26, qty_for_16_25, qty_for_beyond_26,"charges_for_16_25, charges_for_beyond_26, qty_for_16_25, qty_for_beyond_26")
					if qty_for_16_25 > 0:
						item_row=target.append("items",{"item_code":storage_charges_item_16_25,"qty":qty_for_16_25,"rate":charges_for_16_25})
					else:
						frappe.throw(_("You cannot create Tax Invoice for Storage Charges as there are no paid days."))
					if qty_for_beyond_26 > 0:
						item_row=target.append("items",{"item_code":storage_charges_item_beyond_26,"qty":qty_for_beyond_26,"rate":charges_for_beyond_26})
			
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
					"condition":lambda doc:len(doc.name)<0,
					# "postprocess":update_item
				},		
			}, target_doc,set_missing_values)
			doc.run_method("set_missing_values")
			doc.run_method("calculate_taxes_and_totals")
			doc.save()
			frappe.msgprint(_("Tax Invoice of Storage Charges for {0} is created.").format(cargo_item_field),alert=True)	
			return doc.name
		
def get_rate_and_qty_for_actual_storage_type_based_on_storage_report(vessel,customer_name):
	customer_doc=frappe.get_doc('Customer',customer_name)
	if len(customer_doc.get("custom_chargeable_storage_charges_slots_details"))>0:
		first_slot_item=customer_doc.custom_chargeable_storage_charges_slots_details[0].item
		first_slot_storage_charges = get_item_price(first_slot_item) or 0
		print(first_slot_storage_charges,"---first")
		if len(customer_doc.get("custom_chargeable_storage_charges_slots_details"))>1:
			second_slot_item=customer_doc.custom_chargeable_storage_charges_slots_details[1].item
			second_slot_storage_charges = get_item_price(second_slot_item) or 0
			print(second_slot_storage_charges,"---second")
	
	from kict.kict.report.storage_charges.storage_charges import execute
	report_filters = frappe._dict({"vessel":vessel,"customer":customer_name})
	storage_charges_report_data = execute(report_filters)

	first_slot_closing_balance, second_slot_closing_balance = 0,0
	for item in storage_charges_report_data[1]:
		if item.rate == first_slot_storage_charges:
			first_slot_closing_balance = first_slot_closing_balance + item.bal_qty
		if item.rate == second_slot_storage_charges:
			second_slot_closing_balance = second_slot_closing_balance + item.bal_qty
	
	return first_slot_storage_charges, second_slot_storage_charges, first_slot_closing_balance, second_slot_closing_balance


def get_item_price(item_code):
	from erpnext.stock.get_item_details import get_price_list_rate_for
	args=frappe._dict({
		'price_list':"Standard Selling",
		'qty':1,
		'uom':frappe.db.get_value('Item', item_code, 'stock_uom')})
	return get_price_list_rate_for(args,item_code)

@frappe.whitelist()
def get_cargo_handling_rate_for_customer_based_on_billing_type(docname,customer,billing_type)	:
	doctype_name='Vessel'
	item_code_for_si = frappe.db.get_single_value("Coal Settings","ch_charges")
	customer_selling_price_list=get_customer_selling_price_list(customer)
	company = frappe.db.get_value(doctype_name, docname, 'company')
	item_defaults=get_item_defaults(item_code_for_si,company)
	uom=item_defaults.get('stock_uom')
	if uom==None:
		frappe.throw(_("Please set uom of item"))
	args=frappe._dict({
		'customer':customer,
		'price_list':customer_selling_price_list,
		'qty':1,
		'uom':uom})
	item_price= get_price_list_rate_for(args,item_code_for_si)
	percent_billing,is_periodic=get_rate_percent_billing(customer,billing_type)
	calculated_item_price=(item_price*percent_billing)/100
	return calculated_item_price

def get_customer_selling_price_list(customer):
	customer_price_list, customer_group = frappe.get_value(	"Customer", customer, ["default_price_list", "customer_group"])
	customer_group_price_list = frappe.get_value("Customer Group", customer_group, "default_price_list")
	selling_price_list=frappe.db.get_value("Selling Settings", None, "selling_price_list")
	customer_selling_price_list = (	customer_price_list or customer_group_price_list or selling_price_list)
	if customer_selling_price_list==None:
		frappe.throw(_("Please set customer selling price list"))
	return customer_selling_price_list	

def get_rate_percent_billing(customer,billing_type):
	percent_billing_detail = frappe.db.get_list("Cargo Handling Charges Slots Details",
								parent_doctype="Customer",
								filters={"cargo_handling_option_name":billing_type,"parent":customer},
								fields=["percent_billing","is_periodic"])
	if len(percent_billing_detail)>0:
		percent_billing=percent_billing_detail[0].percent_billing
		is_periodic=percent_billing_detail[0].is_periodic
		return percent_billing,is_periodic

@frappe.whitelist()
def get_unique_item(docname):
	items_list = frappe.db.get_list("Vessel Details",
								parent_doctype="Vessel",
								filters={"parent":docname},
								fields=["item"])
	return items_list

@frappe.whitelist()
def get_customer_and_tonnage_based_on_cargo_item(item_code,docname):
	customer_name = frappe.db.get_list("Vessel Details",
								parent_doctype="Vessel",
								filters={"item":item_code,"parent":docname},
								fields=["customer_name","tonnage_mt","customer_po_no"])
	return customer_name

@frappe.whitelist()
def get_cargo_handling_option_name_and_is_periodic_or_not_based_on_customer(docname,customer_name):
	cargo_handling_charges_details = frappe.db.get_all("Cargo Handling Charges Slots Details",
													filters = {"parent":customer_name},
													fields = ["cargo_handling_option_name","billing_type"],
													order_by = "idx")
	return cargo_handling_charges_details

@frappe.whitelist()
def get_from_date_for_dispatch_periodic_type(vessel=None,cargo_item_field=None,type_of_billing_field=None):
	# check SI first
	si_detail = frappe.db.sql(
		"""
			select custom_cargo_from_date as from_date,name from `tabSales Invoice`
			where custom_type_of_cargo_handling_invoice='Periodic'
			and custom_type_of_invoice='Cargo Handling Charges'
			and vessel=%s
			and custom_cargo_item=%s
			and custom_cargo_sub_type_of_invoice=%s 		
			order by custom_cargo_from_date DESC limit 1
		""",(vessel,cargo_item_field,type_of_billing_field),as_dict=1,debug=1
	)	
	print(si_detail,'si_detail')
	if len(si_detail)>0:
		return si_detail[0]
	# check RR
	rr_detail = frappe.db.sql(
		"""
		SELECT rr.rr_date as from_date,rr.name,rr_item.name,rr_item.idx FROM `tabRailway Receipt` as rr 
		inner join `tabRailway Receipt Item Details` as rr_item 
		on rr.name =rr_item.parent 
		where rr.hold_for_invoice=0 and rr_item.is_billed='No' and rr.docstatus=1
		and rr_item.is_dn_created ='Yes'
		and rr_item.vessel = %s
		and rr_item.item = %s
		order by rr_date ASC limit 1
		""",(vessel,cargo_item_field),as_dict=1,debug=1
	)

	print(rr_detail,'rr_detail')
	if len(rr_detail)>0:
		return rr_detail[0]


@frappe.whitelist()
def get_qty_for_dispatch_periodic_type(vessel=None,cargo_item_field=None,from_date_field=None,to_date_field=None):
	print(vessel,cargo_item_field,from_date_field,to_date_field)
	def get_conditions(filters):
		conditions =""

		conditions += " and rr_item.vessel = %(vessel)s"
		conditions += " and rr_item.commercial_destination_item = %(cargo_item_field)s"
		
		conditions += " and rr.rr_date between '{0}' and '{1}'".format(
					filters.get("from_date_field"),
					filters.get("to_date_field")
		)
		return conditions

	filters=frappe._dict(
			{
				"vessel": vessel,
				"cargo_item_field": cargo_item_field,
				"from_date_field": from_date_field,
				"to_date_field": to_date_field,
			} 
        ) 

	conditions = get_conditions(filters)
	print(conditions,"conditions")
	qty_entries = frappe.db.sql(
		"""
		SELECT sum(rr_item.rr_item_weight_mt) as rr_item_weight_mt  FROM `tabRailway Receipt` as rr 
		inner join `tabRailway Receipt Item Details` as rr_item 
		on rr.name =rr_item.parent 
		where rr.hold_for_invoice=0 and rr_item.is_billed='No' and rr.docstatus=1
		and rr_item.is_dn_created ='Yes' {0} group by rr_item.item order by rr_date ASC
		""".format(conditions),filters,as_dict=1,debug=1
	)	
	participating_rr_details=frappe.db.sql(
		"""
		SELECT rr_item.parent,rr_item.name,rr_item.idx,rr_item.rr_item_weight_mt,rr.rr_date  FROM `tabRailway Receipt` as rr 
		inner join `tabRailway Receipt Item Details` as rr_item 
		on rr.name =rr_item.parent 
		where rr.hold_for_invoice=0 and rr_item.is_billed='No' and rr.docstatus=1
		and rr_item.is_dn_created ='Yes' {0} order by rr_date ASC
		""".format(conditions),filters,as_dict=1,debug=1
	)

	if len(participating_rr_details)>0:
		table_body="<table border='1'><tr><td><b>RR Name</b></td><td><b>RR Date</b></td><td><b>Item No</b></td><td><b>Item Weight</b></td></tr>"
		table_row=""
		for item in participating_rr_details:
			table_row=table_row+"<tr><td>"+item.parent+"</td><td>"+cstr(item.rr_date)+"</td><td>"+cstr(item.idx)+"</td><td>"+cstr(item.rr_item_weight_mt)+"</td></tr>"
		table_html=table_body+table_row+"</table>"
	else:
		table_html="<b>No participating railway receipt found.</b>"
	print(table_html,'table_html')
	return qty_entries,table_html,participating_rr_details
	

def get_qty_for_handling_loss_and_audit_shortage(vessel,item_code):
	stock_entry_type_for_handling_loss=frappe.db.get_single_value('Coal Settings', 'handling_loss')
	stock_entry_type_for_audit_shortage=frappe.db.get_single_value('Coal Settings',  'audit_shortage')
	qty_entries = frappe.db.sql(
		"""select 
				ABS(sum(batch_package.qty)) as actual_qty
			from
							`tabStock Ledger Entry` sle
			inner join `tabSerial and Batch Entry` batch_package
						on
							sle.serial_and_batch_bundle = batch_package.parent
			inner join `tabBatch` batch 
						on
				batch_package.batch_no = batch.name
			inner join `tabStock Entry` tse 
						on
				tse.name = sle.voucher_no
			where
							sle.docstatus < 2
				and sle.is_cancelled = 0
				and sle.has_batch_no = 1
				and sle.vessel = '{0}'
				and sle.item_code = '{1}'
				and tse.stock_entry_type in ('{2}', '{3}')
			group by
							sle.vessel,
							sle.item_code				
		""".format(vessel,item_code,stock_entry_type_for_handling_loss,stock_entry_type_for_audit_shortage),as_dict=1,debug=1
	)
	if len(qty_entries)>0:
		return qty_entries[0].actual_qty
	
@frappe.whitelist()
def get_unique_customer_form_vessel(docname):
	return frappe.get_all(
		"Vessel Details",
		parent_doctype="Vessel",
		filters={"parent": docname},
		fields=["distinct customer_name"]
	)

@frappe.whitelist()
def get_item_based_on_customer(docname,customer):
	items_list = frappe.db.get_list("Vessel Details",
								parent_doctype="Vessel",
								filters={"parent":docname,"customer_name":customer},
								fields=["item"])
	return items_list