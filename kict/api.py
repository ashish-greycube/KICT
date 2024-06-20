import frappe
from frappe import _
from frappe.utils import getdate,flt,cstr,add_days,get_first_day,get_last_day
from kict.kict.doctype.railway_receipt.railway_receipt import get_available_batches
from erpnext.stock.get_item_details import get_item_details,get_basic_details,get_price_list_rate_for
from frappe.model.mapper import get_mapped_doc
from frappe.utils import add_days,get_time

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
	time=get_time(time)
	if time <= get_time('06:00:00'):
		return add_days(date,-1)
	elif time > get_time('06:00:00') and time <= get_time('23:59:59'):
		return date
	

@frappe.whitelist()
def create_purchase_invoice_for_royalty_charges(source_name=None,target_doc=None,supplier_name=None,supplier_invoice_no=None,posting_date=None):
	print("create_purchase_invoice_for_royalty_charges----",source_name,supplier_name,supplier_invoice_no,posting_date)
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
			pass
		if currency:
			target.currency = currency

		target.set_posting_time = 1
		target.posting_date = posting_date

		filter__from_date=get_first_day(posting_date)
		filter__to_date=get_last_day(posting_date)
		posting_date_month = getdate(posting_date).month
		filter_date=add_days(posting_date,-32)
		sof_list = frappe.db.get_all("Statement of Fact",
									 or_filters={'first_line_ashore':['between',[filter__from_date,filter__to_date]],
											  'all_line_cast_off':['between',[filter__from_date,filter__to_date]] },          
								   fields=["name","first_line_ashore","all_line_cast_off","current_month_stay_hours"])
		print(sof_list)  
		for sof in sof_list:
			if sof.first_line_ashore and sof.all_line_cast_off:
				first_line_ashore_month,all_line_cast_off_month = (sof.first_line_ashore).month,(sof.all_line_cast_off).month
				if posting_date_month==first_line_ashore_month or posting_date_month==all_line_cast_off_month:
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
				royalty_invoice_item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_foreign_vessel")
				print(royalty_invoice_item)
			if type_of_vessel == "Costal":
				royalty_invoice_item = frappe.db.get_single_value("Coal Settings","birth_hire_item_for_coastal_vessel")
				print(royalty_invoice_item,"Costal")
			
			vessel_item_commodity = frappe.db.get_all("Vessel Details",
													  parent_doctype = "Vessel",
													  filters={"parent":vessel},
													  fields=["coal_commodity"])
			distinct_item_commodity = []
			if len(vessel_item_commodity)>0:
				for row in vessel_item_commodity:
					if row.coal_commodity not in distinct_item_commodity:
						distinct_item_commodity.append(row.coal_commodity)

			print(distinct_item_commodity,"distinct_item_commodity")
			vessel_item_list = ",".join((ele if ele!=None else '') for ele in distinct_item_commodity)
			# for item in vessel_item_commodity:
			#     vessel_item_list.append(item.item)
			print(vessel_item_list)
			
			# item_args=frappe._dict({'item_code':royalty_invoice_item,'buying_price_list':price_list,'company':vessel_doc.company,"doctype":"Purchase Invoice"})
			# item_defaults=get_basic_details(item_args,item=None)
			# args = frappe._dict({'price_list':'Standard Buying','qty':1,'uom':item_defaults.get('stock_uom')})
			# price_list_rate=get_price_list_rate_for(args,royalty_invoice_item)

			bh_rate = get_item_price_list_rate(vessel,royalty_invoice_item,price_list)
			print(bh_rate,"-->price_list_rate")

			current_month_stay_hours = frappe.db.get_value("Statement of Fact",vessel,"current_month_stay_hours")
			print(current_month_stay_hours,"--> ",vessel)
			custom_qty = vessel_doc.grt * current_month_stay_hours
			royalty_percentage = frappe.db.get_single_value("Coal Settings","royalty_percentage")
			custom_amount = custom_qty * bh_rate
			calculated_rate = custom_amount * royalty_percentage
			sof = frappe.db.get_all("Statement of Fact",
						   filters={"name":vessel},
						   fields=["vessel_stay_hours","current_month_stay_hours","next_month_stay_hours","first_line_ashore","all_line_cast_off"])
			actual_berth_hours = None
			print(sof)
			if len(sof)>0:
				first_line_month = (sof[0].first_line_ashore).month
				all_line_month = (sof[0].all_line_cast_off).month
				print(first_line_month,all_line_month)
				if posting_date_month==first_line_month and posting_date_month==all_line_month:
					actual_berth_hours = sof[0].vessel_stay_hours
					print("all month same ------------")
				elif posting_date_month == first_line_month:
					actual_berth_hours = sof[0].current_month_stay_hours
					print("first line same ==============")
				elif posting_date_month == all_line_month:
					actual_berth_hours = sof[0].next_month_stay_hours
					print("all line same ************************")

			purchase_invoice_item_bh = target.append("items",
			{"item_code":royalty_invoice_item,"custom_vessel_name":vessel,"custom_commodity":vessel_item_list,"custom_grt":vessel_doc.grt,
			"custom_current_month_stay_hours":current_month_stay_hours,"custom_custom_qty":custom_qty,"rate":calculated_rate,"custom_actual_berth_hours":actual_berth_hours})

			royalty_invoice_item = frappe.db.get_single_value("Coal Settings","ch_charges")
			cargo_handling_data = get_cargo_handling_qty_for_royalty_purchase_invoice(posting_date)
			if len(cargo_handling_data)>0:
				for row in cargo_handling_data:
					if row.get("vessel") == vessel:
						ch_price_list_rate = get_item_price_list_rate(vessel,royalty_invoice_item,price_list)
						qty = vessel_doc.total_tonnage_mt
						ch_amount = qty * ch_price_list_rate
						ch_rate = ch_amount * royalty_percentage

						purchase_invoice_item_ch =target.append("items",
						{"item_code":royalty_invoice_item,"custom_vessel_name":vessel,"custom_commodity":row.get("item"),"custom_grt":vessel_doc.total_tonnage_mt,
						"custom_current_month_stay_hours":current_month_stay_hours,"custom_custom_qty":vessel_doc.total_tonnage_mt,"rate":ch_rate,"custom_actual_berth_hours":actual_berth_hours})
	
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
	doc.save(ignore_permissions=True)
	# if is_periodic_or_dispatch_field=='Periodic':
	# 	rr_details = get_qty_for_dispatch_periodic_type(source_name,cargo_item_field,from_date_field,to_date_field)
	# 	participating_rr_details = rr_details[2]
	# 	for ele in participating_rr_details:
	# 		frappe.db.set_value("Railway Receipt Item Details",ele.name,"is_billed","Yes")
	# 		frappe.db.set_value("Railway Receipt Item Details",ele.name,"sales_invoice_reference",doc.name)
	return doc.name


def get_cargo_handling_qty_for_royalty_purchase_invoice(posting_date):
		from frappe.utils.data import get_date_str

		month_start_date=get_first_day(posting_date)
		port_start_date_with_time=get_date_str(month_start_date)+' 06:00:01'

		next_month_start_date = add_days(get_last_day(posting_date),1)
		port_end_date_with_time=get_date_str(next_month_start_date)+' 06:00:00'

		query = frappe.db.sql(
		"""			select 
				sle.vessel,
				sle.item_code,		
				sum(batch_package.qty) as actual_qty				
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
				and sle.posting_datetime >='{0}'
				and sle.posting_datetime <='{1}'
			group by
				sle.vessel ,sle.item_code """.format(port_start_date_with_time,port_end_date_with_time),as_dict=1,debug=1)	
		data=[]
		vessel_done=[]
		if len(query)>0:
			for row in query:
				current_vessel=row.vessel
				current_vessel_qty=0
				current_vessel_item=[]
				if current_vessel not in vessel_done:
					for inner_row in query:
						if inner_row.vessel==current_vessel:
							current_vessel_qty=current_vessel_qty+inner_row.actual_qty
							current_vessel_comodity = frappe.db.get_value('Item', inner_row.item_code, 'custom_coal_commodity')
							if  current_vessel_comodity not in current_vessel_item:
								current_vessel_item.append(current_vessel_comodity)							
					vessel_done.append(current_vessel)	
					data.append({'vessel':current_vessel,'qty':current_vessel_qty,'item':",".join(current_vessel_item)})
		return data

def get_item_price_list_rate(vessel,royalty_invoice_item,price_list):
	vessel_doc = frappe.get_doc("Vessel",vessel)
	item_args=frappe._dict({'item_code':royalty_invoice_item,'buying_price_list':price_list,'company':vessel_doc.company,"doctype":"Purchase Invoice"})
	item_defaults=get_basic_details(item_args,item=None)
	args = frappe._dict({'price_list':'Standard Buying','qty':1,'uom':item_defaults.get('stock_uom')})
	price_list_rate=get_price_list_rate_for(args,royalty_invoice_item)
	print(price_list_rate,"-->price_list_rate")
	return price_list_rate

