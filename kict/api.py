import frappe
from frappe import _
from frappe.utils import getdate,flt,cstr,add_days,get_first_day,get_last_day
from kict.kict.doctype.railway_receipt.railway_receipt import get_available_batches
from erpnext.stock.get_item_details import get_item_details,get_basic_details
from frappe.model.mapper import get_mapped_doc


def set_cargo_handling_option_name_and_is_periodic(self,method):
	for row in self.get("custom_cargo_handling_charges_slots_details"):
		option = str(row.percent_billing)+ "%" + " - " +row.billing_when
		row.cargo_handling_option_name = option
		billing_type = row.billing_when
		posotion_of_string_for_periodic = billing_type.find("Periodic")
		posotion_of_string_for_dispatch = billing_type.find("Dispatch")

		if posotion_of_string_for_periodic >= 0:
			row.billing_type = "Periodic"
		elif posotion_of_string_for_dispatch >= 0:
			row.billing_type = "Dispatch"
		else:
			row.billing_type = "Non-Periodic"

def validate_rate_percent_billing(self,method):
	total_percent = 0
	if len(self.get("custom_cargo_handling_charges_slots_details")) > 0:
		for row in self.get("custom_cargo_handling_charges_slots_details"):
			total_percent = total_percent + row.percent_billing
	
		if total_percent != 100:
			frappe.throw(_("Total of Rate Percent Billing must be 100%"))
		else:
			pass

def change_status_for_dn_creation_in_railway_receipt_on_cancel_of_dn(self,method):
	frappe.db.set_value("Railway Receipt Item Details",self.custom_railway_receipt_detail,"is_dn_created","No")

def change_status_for_is_billed_in_on_cancel_of_si(self,method):
	if self.custom_type_of_cargo_handling_invoice and self.custom_type_of_cargo_handling_invoice=="Periodic":    
		participating_rr = frappe.db.get_all("Railway Receipt Item Details",
											filters = {"sales_invoice_reference":self.name},
											fields = ["name","is_billed","sales_invoice_reference"])
		for ele in participating_rr:
			frappe.db.set_value("Railway Receipt Item Details",ele.name,"is_billed","No")
			frappe.db.set_value("Railway Receipt Item Details",ele.name,"sales_invoice_reference","")

def copy_vessel_to_stock_entry_item(self,method):
	vessel=self.custom_vessel
	for item in self.get("items"):
		item.to_vessel=vessel

def copy_source_vessel_to_stock_entry_item(self,method):
	vessel=self.custom_vessel
	for item in self.get("items"):
		item.vessel=vessel

def set_batch_no_and_warehouse_for_handling_loss_audit_sortage(self,method):
	if self.stock_entry_type=="Audit Shortage" or self.stock_entry_type=="Handling Loss":
		copy_source_vessel_to_stock_entry_item(self,method)
		item_table_with_batches=[]
		item_rows_to_be_removed=[]
		for item in self.get("items"):
			if item.batch_no!=None:
				pass
			elif item.batch_no==None:    
				args=frappe._dict({'item_code': item.item_code, 
				'has_serial_no': '0', 
				'has_batch_no': '1', 
				'qty':item.qty, 
				'based_on': 'FIFO', 
				'vessel':self.custom_vessel,
				# 'posting_date': self.posting_date,
				# 'posting_time': self.posting_time,
				'cmd': "kict.kict.doctype.railway_receipt.railway_receipt.get_auto_data"
				}) 
				available_batches=get_available_batches(args)               
				# check if batch total qty is less than required qty
				qty_from_batches=0
				for batch in available_batches:
					qty_from_batches=qty_from_batches+batch.qty
				if len(available_batches) < 1:
					table_html = frappe.bold("No batches found.")
					msg="The qty available from batches is {0}, whereas required qty is {1}. Hence cannot proceed.".format(frappe.bold(qty_from_batches),frappe.bold(item.qty))	
					frappe.throw(_(table_html+"<br>"+msg))				
				if item.qty>qty_from_batches:
					table_body="<table border='1'><tr><td><b>Batch</b></td><td><b>Warehouse</b></td><td><b>Qty</b></td></tr>"
					table_row=""
					for item in available_batches:
						table_row=table_row+"<tr><td>"+item.batch_no+"</td><td>"+item.warehouse+"</td><td>"+cstr(item.qty)+"</td></tr>"
					table_html=table_body+table_row+"</table>"			
					msg="The qty available from batches is {0}, whereas required qty is {1}. Hence cannot proceed.".format(frappe.bold(qty_from_batches),frappe.bold(item.qty))	
					frappe.throw(_(table_html+"<br>"+msg))
				# for each batch, warehouse add seperate line item
				for batch in available_batches:
					item_with_batch={'item_code':item.item_code,
									 'item_name':item.item_name,
									 'custom_customer':item.custom_customer,
									 'description':item.description,
									 'item_group':item.item_group,
									 'uom':item.uom,
									 'stock_uom':item.stock_uom,
									 'transfer_qty':batch.qty,
									 'conversion_factor':item.conversion_factor,
									 'qty':batch.qty,
									 'batch_no':batch.batch_no,
									 's_warehouse':batch.warehouse,
									 'vessel':self.custom_vessel,}
					item_table_with_batches.append(item_with_batch)
				
				item_rows_to_be_removed.append(item)
			   
		if len(item_table_with_batches)>0:
			[self.items.remove(d) for d in item_rows_to_be_removed]
			for row in item_table_with_batches:
				frappe.msgprint(_('Item {0} has now batch {1} and source warehouse {2}').format(row.get('item_code'),row.get('batch_no'),row.get('s_warehouse')),alert=True)
				self.append("items",row)

def generate_and_set_batch_no(self,method):
	if self.stock_entry_type=="Cargo Received":
		copy_vessel_to_stock_entry_item(self,method)
		for item in self.get("items"):
			if item.batch_no==None:
				batch_name=check_batch_no_exist(item.to_vessel,item.item_code,self.posting_date,self.posting_time)
				if batch_name!=None:
					item.batch_no=batch_name
					frappe.msgprint(_('Item {0} existing  batch {1} is added').format(item.item_code,item.batch_no),alert=True)
				else:
					batch_name=generate_batch_no(item.to_vessel,item.item_code,self.posting_date,self.posting_time)
					item.batch_no=batch_name
					frappe.msgprint(_('Item {0} new batch {1} is added').format(item.item_code,item.batch_no),alert=True)

def check_batch_no_exist(vessel,item_code,posting_date,posting_time):
	port_date=get_port_date(posting_date,posting_time)
	batch_name=None
	batch_found = frappe.db.get_list("Batch", 
			filters={"item":item_code,"custom_vessel":vessel,"manufacturing_date":port_date},
			fields=["name"]) 
	if len(batch_found)>0:
		batch_name=batch_found[0].name
	return batch_name

	

def generate_batch_no(vessel,item_code,posting_date,posting_time):
	port_date=get_port_date(posting_date,posting_time)
	is_customer_provided_item = frappe.db.get_value('Item', item_code, 'is_customer_provided_item')
	if is_customer_provided_item==0:
		return
	def make_batch(kwargs):
		if frappe.db.get_value("Item", kwargs.item, "has_batch_no"):
			if frappe.db.get_value("Item", kwargs.item, "is_customer_provided_item"):
				if frappe.db.get_value("Item", kwargs.item, "create_new_batch")==0:
					kwargs.doctype = "Batch"
					return frappe.get_doc(kwargs).insert().name
		
	batch_id=get_name_from_hash(port_date,item_code)
	batch_name= make_batch(frappe._dict({
				"batch_id":batch_id,
				"item": item_code,
				"custom_vessel":vessel,
				"manufacturing_date":port_date,
				"stock_uom":frappe.db.get_value('Item', item_code, 'stock_uom'),
				"use_batchwise_valuation":0
			}
		)
	)    
	return batch_name

def get_name_from_hash(port_date,item_code):
	current_date=getdate(port_date).strftime("%d.%m.%y")
	print('current_date',current_date)
	coal_commodity = frappe.db.get_value("Item",item_code,"custom_coal_commodity")
	commodity_grade = frappe.db.get_value("Item",item_code,"custom_commodity_grade")
	customer_abbreviation = frappe.db.get_value("Item",item_code,"custom_customer_abbreviation")
	"""
	Get a name for a Batch by generating a unique hash.
	:return: The hash that was generated.
	"""
	temp = None
	while not temp:
		temp = coal_commodity[:1].upper()+commodity_grade[:1].upper()+customer_abbreviation+"-"+current_date+"-"+frappe.generate_hash()[:2].upper()
		if frappe.db.exists("Batch", temp):
			temp = None
	return temp

def set_grt_billed_for_bh_in_vessel_detail_on_submit_of_si(self,method):
	if self.custom_type_of_invoice == "Berth Hire Charges":
		vessel_doc = frappe.get_doc("Vessel",self.vessel)
		customer_specific_total_tonnage = calculate_customer_specific_total_tonnage(self,method)
		for row in vessel_doc.get("vessel_details"):
			if row.customer_name==self.customer:
				billed_qty = (flt((customer_specific_total_tonnage),3) / flt((self.custom_quantity_in_mt),3) ) * flt((row.tonnage_mt),3)
				row.grt_billed_for_bh_for_si = billed_qty

		vessel_doc.save(ignore_permissions = True)

def set_grt_billed_for_bh_in_vessel_detail_on_submit_of_pi(self,method):
	if self.custom_type_of_invoice == "Berth Hire Charges":
		vessel_doc = frappe.get_doc("Vessel",self.vessel)
		customer_specific_total_tonnage = calculate_customer_specific_total_tonnage(self,method)
		for row in vessel_doc.get("vessel_details"):
			if row.customer_name==self.customer:
				billed_qty = (flt((customer_specific_total_tonnage),3) / flt((self.custom_quantity_in_mt),3) ) * flt((row.tonnage_mt),3)
				row.grt_billed_for_bh_for_pi = billed_qty

		vessel_doc.save(ignore_permissions = True)

def calculate_customer_specific_total_tonnage(self,method):
	vessel_doc = frappe.get_doc("Vessel",self.vessel)
	customer_specific_total_tonnage = 0
	for item in vessel_doc.get("vessel_details"):
		if item.customer_name==self.customer:
			customer_specific_total_tonnage = customer_specific_total_tonnage + item.tonnage_mt
	return customer_specific_total_tonnage

def validate_vessel_is_not_closed_in_stock_entry(self,method):
	vessel_name = self.custom_vessel
	vessel_closure_value = frappe.db.get_value("Vessel",vessel_name,"vessel_closure")
	if vessel_closure_value == 1:
		frappe.throw(_("Vessel {0} is closed. You can not create Stock Entry.").format(frappe.bold(vessel_name)))

	for item in self.items:
		item_detail = frappe.db.get_all("Vessel Details",
										parent_doctype = "Vessel",
										filters={"parent":vessel_name,"item":item.item_code},
										fields=["cargo_closure"])
		if len(item_detail)>0:
			if item_detail[0].cargo_closure == 1:
				frappe.throw(_("Row# {0} : vessel {1} and cargo item {2} is closed. You can not create stock entry.")
							 .format(item.idx,frappe.bold(vessel_name),frappe.bold(item.item_code)))

def validate_vessel_is_not_closed_in_delivery_note(self,method):
	for item in self.items:
		vessel_name = item.vessel
		vessel_closure_value = frappe.db.get_value("Vessel",vessel_name,"vessel_closure")
		if vessel_closure_value == 1:
			frappe.throw(_("Vessel {0} is closed. You can not create Stock Entry.").format(frappe.bold(vessel_name)))        
		vessel_item = frappe.db.get_all("Vessel Details",
										parent_doctype = "Vessel",
										filters={"parent":vessel_name,"item":item.item_code},
										fields=["cargo_closure"])
		if len(vessel_item)>0:
			if vessel_item[0].cargo_closure == 1:
				frappe.throw(_("Row #{0}: vessel {1} and item {2} is closed. You can not create Delivery Note.")
							 .format(item.idx,frappe.bold(vessel_name),frappe.bold(item.item_code)))
				
def create_purchase_invoice_for_royalty(self, method):
	return
	print("="*10,method)
	eligible_vessels=[]
	if self.supplier and self.posting_date and self.custom_is_royalty_invoice == 1 :
		filter__from_date=get_first_day(self.posting_date)
		filter__to_date=get_last_day(self.posting_date)
		posting_date_month = getdate(self.posting_date).month
		filter_date=add_days(self.posting_date,-32)
		sof_list = frappe.db.get_all("Statement of Fact",
									 filters={'first_line_ashore':['between',[filter__from_date,filter__to_date]],
											  'all_line_cast_off':['between',[filter__from_date,filter__to_date]] },          
								   fields=["name","first_line_ashore","all_line_cast_off","current_month_stay_hours"])
		print(sof_list)  
		for sof in sof_list:
			if sof.first_line_ashore and sof.all_line_cast_off:
				first_line_ashore_month,all_line_cast_off_month = (sof.first_line_ashore).month,(sof.all_line_cast_off).month
				if posting_date_month==first_line_ashore_month and posting_date_month==all_line_cast_off_month:
					eligible_vessels.append(sof.name)

		if len(eligible_vessels)==0:
			frappe.throw("No eligible vessels found for {0} month".format(posting_date_month))
		# self.bill_no = ''
		print("Condition satisfy",eligible_vessels)
		for vessel in eligible_vessels:
			print(vessel)
			vessel_doc = frappe.get_doc("Vessel",vessel)
			type_of_vessel = vessel_doc.costal_foreign_vessle
			print(type_of_vessel,"---------")
			if type_of_vessel == "Foreign":
				invoice_item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_foreign_vessel")
				print(invoice_item)
			if type_of_vessel == "Costal":
				invoice_item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_coastal_vessel")
				print(invoice_item,"Costal")
			
			vessel_item_commodity = frappe.db.get_all("Vessel Details",
													  parent_doctype = "Vessel",
													  filters={"parent":vessel},
													  fields=["item"])
			vessel_item_list = ",".join((ele.item if ele.item!=None else '') for ele in vessel_item_commodity)
			# for item in vessel_item_commodity:
			#     vessel_item_list.append(item.item)
			print(vessel_item_list)
			
			royalty_price_list = frappe.db.get_single_value('Coal Settings', 'royalty_price_list')

			item_args=frappe._dict({'item_code':invoice_item,'buying_price_list':royalty_price_list,'company':vessel_doc.company,"doctype":"Purchase Invoice"})
			item_defaults=get_basic_details(item_args,item=None)
			print(item_defaults,'='*10)
			current_month_stay_hours = frappe.db.get_value("Statement of Fact",vessel,"current_month_stay_hours")


			custom_qty = vessel_doc.grt * current_month_stay_hours
			item_row = self.append("items",{})
			item_row.item_name = invoice_item
			item_row.custom_vessel_name= vessel
			item_row.custom_commodity= vessel_item_list
			item_row.custom_grt= vessel_doc.grt
			item_row.custom_current_month_stay_hours= current_month_stay_hours
			item_row.custom_custom_qty= custom_qty
			item_row.custom_actual_berth_hours= current_month_stay_hours
			item_row.qty = 1
			item_row.uom = item_defaults.stock_uom
			item_row.conversion_factor = item_defaults.conversion_factor
			item_row.stock_qty = item_defaults.stock_qty
			item_row.rate = item_defaults.rate
			item_row.amount = 0
			item_row.base_rate = item_defaults.base_rate
			item_row.base_amount = item_defaults.base_amount
			item_row.expense_account = "Cost of Goods Sold - KICTPPL"


def remove_calculation_for_percent_billing_on_cancel_of_si(self,method):
	if self.custom_type_of_invoice == "Berth Hire Charges":
		vessel_doc = frappe.get_doc("Vessel",self.vessel)
		for row in vessel_doc.get("vessel_details"):
			if row.customer_name==self.customer:
				row.grt_billed_for_bh_for_si = 0

		vessel_doc.save(ignore_permissions = True)

def remove_calculation_for_percent_billing_on_cancel_of_pi(self,method):
	if self.custom_type_of_invoice == "Berth Hire Charges":
		vessel_doc = frappe.get_doc("Vessel",self.vessel)
		for row in vessel_doc.get("vessel_details"):
			if row.customer_name==self.customer:
				row.grt_billed_for_bh_for_pi = 0

		vessel_doc.save(ignore_permissions = True)

def get_port_date(date,time):
    from frappe.utils import add_days
    if time <= '06:00:00':
        return add_days(date,-1)
    elif time > '06:00:00' and time <= '24:00:00':
        return date
	

@frappe.whitelist()
def create_purchase_invoice_for_royalty_charges(source_name=None,target_doc=None,supplier_name=None,supplier_invoice_no=None,posting_date=None):
	print("create_purchase_invoice_for_royalty_charges")
	source_name = frappe.get_last_doc('Vessel').name
	def set_missing_values(source, target):
		eligible_vessels = []
		target.supplier = supplier_name
		target.bill_no = supplier_invoice_no
		target.custom_is_royalty_invoice = 1
		price_list= frappe.db.get_single_value("Coal Settings", "royalty_price_list")
		currency= frappe.db.get_value("Supplier", {"name": supplier_name}, ["default_currency"])
		if price_list:
			target.buying_price_list = price_list
		if currency:
			target.currency = currency

		target.set_posting_time = 1
		target.posting_date = posting_date

		filter__from_date=get_first_day(posting_date)
		filter__to_date=get_last_day(posting_date)
		posting_date_month = getdate(posting_date).month
		filter_date=add_days(posting_date,-32)
		sof_list = frappe.db.get_all("Statement of Fact",
									 filters={'first_line_ashore':['between',[filter__from_date,filter__to_date]],
											  'all_line_cast_off':['between',[filter__from_date,filter__to_date]] },          
								   fields=["name","first_line_ashore","all_line_cast_off","current_month_stay_hours"])
		print(sof_list)  
		for sof in sof_list:
			if sof.first_line_ashore and sof.all_line_cast_off:
				first_line_ashore_month,all_line_cast_off_month = (sof.first_line_ashore).month,(sof.all_line_cast_off).month
				if posting_date_month==first_line_ashore_month and posting_date_month==all_line_cast_off_month:
					eligible_vessels.append(sof.name)

		if len(eligible_vessels)==0:
			frappe.throw("No eligible vessels found for {0} month".format(posting_date_month))
		# self.bill_no = ''
		print("Condition satisfy",eligible_vessels)
		for vessel in eligible_vessels:
			print(vessel)
			vessel_doc = frappe.get_doc("Vessel",vessel)
			type_of_vessel = vessel_doc.costal_foreign_vessle
			print(type_of_vessel,"---------")
			if type_of_vessel == "Foreign":
				bh_invoice_item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_foreign_vessel")
				print(bh_invoice_item)
			if type_of_vessel == "Costal":
				bh_invoice_item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_coastal_vessel")
				print(bh_invoice_item,"Costal")
			
			vessel_item_commodity = frappe.db.get_all("Vessel Details",
													  parent_doctype = "Vessel",
													  filters={"parent":vessel},
													  fields=["item"])
			vessel_item_list = ",".join((ele.item if ele.item!=None else '') for ele in vessel_item_commodity)
			# for item in vessel_item_commodity:
			#     vessel_item_list.append(item.item)
			print(vessel_item_list)
			
			item_args=frappe._dict({'item_code':bh_invoice_item,'buying_price_list':price_list,'company':vessel_doc.company,"doctype":"Purchase Invoice"})
			# item_defaults=get_basic_details(item_args,item=None)
			# print(item_defaults,'='*10)
			current_month_stay_hours = frappe.db.get_value("Statement of Fact",vessel,"current_month_stay_hours")
			custom_qty = vessel_doc.grt * current_month_stay_hours
			purchase_invoice_item = target.append("items",{"item_code":bh_invoice_item,"custom_vessel_name":vessel,"custom_commodity":vessel_item_list,"custom_grt":vessel_doc.grt,"custom_current_month_stay_hours":current_month_stay_hours,"custom_custom_qty":custom_qty})
	
	doc = get_mapped_doc('Vessel', source_name, {
		'Vessel': {
			'doctype': 'Purchase Invoice',
			# 'field_map': {
			# 	'agent_name':'name',
			# },			
			'validation': {
				'docstatus': ['!=', 2]
			}
		},
		"Vessel Details": {
			"doctype": "Purchase Invoice Item",
			"condition":lambda doc:len(doc.name)<0,
			# "postprocess":update_item
		},		
	}, target_doc,set_missing_values)
	doc.run_method("set_missing_values")
	doc.run_method("calculate_taxes_and_totals")

	# if is_periodic_or_dispatch_field=='Periodic':
	# 	rr_details = get_qty_for_dispatch_periodic_type(source_name,cargo_item_field,from_date_field,to_date_field)
	# 	participating_rr_details = rr_details[2]
	# 	for ele in participating_rr_details:
	# 		frappe.db.set_value("Railway Receipt Item Details",ele.name,"is_billed","Yes")
	# 		frappe.db.set_value("Railway Receipt Item Details",ele.name,"sales_invoice_reference",doc.name)
	return doc