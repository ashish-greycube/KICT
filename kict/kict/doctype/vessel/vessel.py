# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import _
from frappe.utils import flt
from frappe.utils import today
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.stock.get_item_details import get_price_list_rate_for


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
													 customer_specific_grt_percentage=None,customer_specific_grt_field=None,customer_po_no_field=None,bill_hours=None,doctype=None):
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
		target.po_no = customer_po_no_field

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
														customer_specific_grt_percentage=None,customer_specific_grt_field=None,customer_po_no_field=None,bill_hours=None,doctype=None):
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
		target.po_no = customer_po_no_field

		vessel_type = frappe.db.get_value(doctype,source_name,"costal_foreign_vessle")
		if vessel_type == "Foreign":
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_foreign_vessel")
			item_code = item
		else :
			item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_coastal_vessel")
			item_code = item

		target.append("items",{"item_code":item_code,"qty":qty,"custom_grt":customer_specific_grt_field,"custom_actual_hours_of_stay":bill_hours})
	
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
def create_sales_invoice_for_cargo_handling_charges_from_vessel(source_name, target_doc=None,cargo_item_field=None,customer_name_field=None,is_periodic_or_dispatch_field=None,rate_field=None,periodic_cargo_qty=None,non_periodic_cargo_qty=None,customer_po_no_field=None,from_date_field=None,to_date_field=None,doctype=None):
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
		target.custom_type_of_invoice="Cargo Handling Charges"
		if is_periodic_or_dispatch_field=="Non-Periodic":
			target.custom_type_of_cargo_handling_invoice="Non-Periodic"
		else:
			target.custom_type_of_cargo_handling_invoice="Periodic"
			target.custom_cargo_from_date = from_date_field
			target.custom_cargo_to_date = to_date_field
		target.customer=customer_name_field
		target.due_date = today()		
		target.vessel=source_name
		target.po_no = customer_po_no_field
		item_code = frappe.db.get_single_value("Coal Settings","ch_charges")

		# nothing on vessel type
		if is_periodic_or_dispatch_field=="Non-Periodic":
			item_row=target.append("items",{"item_code":item_code,"qty":flt(non_periodic_cargo_qty),"description":cargo_item_field,"rate":rate_field})
		else:
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
	return doc.name

@frappe.whitelist()
def create_sales_invoice_for_storage_charges_from_vessel(source_name, target_doc=None,cargo_item_field=None,customer_name_field=None,total_tonnage_field=None,customer_po_no_field=None,doctype=None):
	from erpnext.stock.report.stock_balance.stock_balance import execute
	
	company_name=frappe.get_value(doctype,source_name,"company")
	filter_for_lv =frappe._dict({"company":company_name,"from_date":today(),"to_date":today(),"item_code":cargo_item_field,"valuation_field_type":"Currency","vessel":[source_name]})
	data = execute(filter_for_lv)

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
				item_code = frappe.db.get_single_value("Coal Settings","storage_charges_fixed")

				# nothing on vessel type

				item_row=target.append("items",{"item_code":item_code,"qty":2*flt(total_tonnage_field),"description":cargo_item_field})
			
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
													fields = ["cargo_handling_option_name","billing_type"])
	return cargo_handling_charges_details

@frappe.whitelist()
def get_from_date_for_dispatch_periodic_type(vessel=None,cargo_item_field=None,type_of_billing_field=None):
	# check SI first
	si_detail = frappe.db.sql(
		"""
			select custom_cargo_from_date as from_date,name from `tabSales Invoice`
			where custom_type_of_cargo_handling_invoice='Periodic'
			and custom_type_of_invoice='Cargo Handling Charges'
			and vessel='%s'
			and custom_cargo_item='%s'
			and custom_cargo_sub_type_of_invoice='%s' 		
		""".format(vessel,cargo_item_field,type_of_billing_field),as_dict=1,debug=1
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
		where rr.hold_for_invoice=0 and rr_item.is_billed='Yes' and rr.docstatus=1
		and rr_item.is_dn_created ='Yes'
		and rr_item.vessel = %s
		and rr_item.item = %s
		order by rr_date DESC limit 1
		""".format(vessel,cargo_item_field),as_dict=1,debug=1
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
		conditions += " and rr_item.item = %(cargo_item_field)s"
		
		conditions += " and rr.rr_date between {0} and {1}".format(
					filters.get("from_date_field"),
					filters.get("to_date_field")
		)
		return conditions

	filters=frappe._dict(
			{
				"vessel": vessel,
				"cargo_item_field": cargo_item_field,
				"from_date": from_date_field,
				"to_date": to_date_field,
			} 
        ) 

	conditions = get_conditions(filters)
	entries = frappe.db.sql(
		"""
		SELECT sum(rr_item.rr_item_weight_mt) as rr_item_weight_mt  FROM `tabRailway Receipt` as rr 
		inner join `tabRailway Receipt Item Details` as rr_item 
		on rr.name =rr_item.parent 
		where rr.hold_for_invoice=0 and rr_item.is_billed='No' and rr.docstatus=1
		and rr_item.is_dn_created ='Yes' 
		{0} order by rr_date ASC
		group by rr_item.item
		""".format(conditions),filters,as_dict=1,debug=1
	)	
	print('entries',entries)
	return entries