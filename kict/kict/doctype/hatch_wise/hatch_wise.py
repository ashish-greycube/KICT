# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Hatchwise(Document):
	def validate(self):
		self.set_balance_qty()
		self.validate_duplicate_entry_of_hatch()

	def set_balance_qty(self):
		for row in self.get("hatch_wise_details"):
			row.balance_qty = (row.arrival_qty or 0) - (row.discharged_qty or 0)
			
	def validate_duplicate_entry_of_hatch(self):
		details = self.get("hatch_wise_details")
		hatch = []
		for ele in details:
			if ele.hatch not in hatch:
				hatch.append(ele.hatch)
			else:
				frappe.throw(_("Row{0}: You cannot select {1} again").format(ele.idx,ele.hatch))


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_unique_grade_list(doctype, txt, searchfield, start, page_len, filters):
	vessel = filters.get("vessel")
	return frappe.get_all(
		"Vessel Details",
		parent_doctype="Vessel",
		filters={"parent": vessel},
		fields=["distinct item_group"],
		as_list=1,
	)