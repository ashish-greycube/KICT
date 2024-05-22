import frappe

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
