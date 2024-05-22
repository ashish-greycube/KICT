import frappe
from frappe import _

def set_cargo_handling_option_name_and_is_periodic(self,method):
    for row in self.get("custom_cargo_handling_charges_slots_details"):
        option = str(row.percent_billing)+ "%" + " - " +row.billing_when
        row.cargo_handling_option_name = option
        billing_type = row.billing_when
        posotion_of_string = billing_type.find("Periodic")
        if posotion_of_string >= 0:
            row.is_periodic = "YES"
        else:
            row.is_periodic = "NO"

def validate_rate_percent_billing(self,method):
    total_percent = 0
    for row in self.get("custom_cargo_handling_charges_slots_details"):
        total_percent = total_percent + row.percent_billing
    
    if total_percent < 100:
        frappe.throw(_("Total of Rate Percent Billing must be 100%"))
    else:
        pass
