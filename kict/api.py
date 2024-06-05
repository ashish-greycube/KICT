import frappe
from frappe import _
from frappe.utils import getdate


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

def generate_and_set_batch_no(self,method):
    if self.stock_entry_type=="Cargo Received":
        copy_vessel_to_stock_entry_item(self,method)
        for item in self.get("items"):
            if item.batch_no==None:
                batch_name=check_batch_no_exist(item.to_vessel,item.item_code,self.posting_date)
                if batch_name!=None:
                    item.batch_no=batch_name
                else:
                    batch_name=generate_batch_no(item.to_vessel,item.item_code,self.posting_date)
                    item.batch_no=batch_name

def check_batch_no_exist(vessel,item_code,posting_date):
    batch_name=None
    batch_found = frappe.db.get_list("Batch", 
            filters={"item":item_code,"custom_vessel":vessel,"manufacturing_date":posting_date},
            fields=["name"]) 
    if len(batch_found)>0:
        batch_name=batch_found[0].name
    return batch_name

    

def generate_batch_no(vessel,item_code,posting_date):
    is_customer_provided_item = frappe.db.get_value('Item', item_code, 'is_customer_provided_item')
    if is_customer_provided_item==0:
        return
    def make_batch(kwargs):
        if frappe.db.get_value("Item", kwargs.item, "has_batch_no"):
            if frappe.db.get_value("Item", kwargs.item, "is_customer_provided_item"):
                if frappe.db.get_value("Item", kwargs.item, "create_new_batch")==0:
                    kwargs.doctype = "Batch"
                    return frappe.get_doc(kwargs).insert().name
        
    batch_id=get_name_from_hash(posting_date,item_code)
    batch_name= make_batch(frappe._dict({
                "batch_id":batch_id,
                "item": item_code,
                "custom_vessel":vessel,
                "manufacturing_date":posting_date,
                "stock_uom":frappe.db.get_value('Item', item_code, 'stock_uom'),
                "use_batchwise_valuation":0
            }
        )
    )    
    return batch_name

def get_name_from_hash(posting_date,item_code):
    current_date=getdate(posting_date).strftime("%d.%m.%y")
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