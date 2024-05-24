import frappe
from frappe import _

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
    for row in self.get("custom_cargo_handling_charges_slots_details"):
        total_percent = total_percent + row.percent_billing
    
    if total_percent != 100:
        frappe.throw(_("Total of Rate Percent Billing must be 100%"))
    else:
        pass
