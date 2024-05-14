# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RakeDispatch(Document):
	pass


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_unique_grade_list(doctype, txt, searchfield, start, page_len, filters):
	vcn_no = filters.get("vessel_name")
	return frappe.get_all(
		"Vessel Details",
		parent_doctype="Vessel",
		filters={"parent": vcn_no},
		fields=["distinct grade"],
		as_list=1,
	)