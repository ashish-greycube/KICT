# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import date_diff,flt
from frappe.model.document import Document


class EquipmentsInandOut(Document):
	def validate(self):
		self.set_total_engaged_time()
		self.set_all_fast()
		
	def set_total_engaged_time(self):	
		for row in self.get("equipemnts_in_and_out_details"):
			if row.equipment_in_date_time and row.equipment_out_date_time:
				end_date = row.equipment_out_date_time
				start_date = row.equipment_in_date_time
				diff=frappe.utils.time_diff_in_seconds(end_date,start_date)
				row.total_engaged_time = diff
	
	def set_all_fast(self):
		sof = frappe.db.get_list("Statement of Fact",filters ={"name":self.vessel},fields=["vessel_made_all_fast"])
		if len(sof) > 0:
			self.all_fast = sof[0].vessel_made_all_fast

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_unique_commodity(doctype, txt, searchfield, start, page_len, filters):
	vessel = filters.get("vessel")
	return frappe.get_all(
		"Vessel Details",
		parent_doctype="Vessel",
		filters={"parent": vessel},
		fields=["distinct item"],
		as_list=1,
	)