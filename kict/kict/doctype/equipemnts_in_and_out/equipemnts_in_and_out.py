# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import date_diff,flt
from frappe.model.document import Document


class EquipemntsInandOut(Document):
	def validate(self):
		self.set_total_engaged_time()
		
	def set_total_engaged_time(self):	
		for row in self.get("equipemnts_in_and_out_details"):
			if row.equipment_in_date_time and row.equipment_out_date_time:
				end_date = row.equipment_out_date_time
				start_date = row.equipment_in_date_time
				diff=frappe.utils.time_diff_in_seconds(end_date,start_date)
				row.total_engaged_time = diff

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_unique_commodity(doctype, txt, searchfield, start, page_len, filters):
	vessel = filters.get("vessel")
	return frappe.get_all(
		"Vessel Details",
		filters={"parent": vessel},
		fields=["distinct commodity"],
		as_list=1,
	)