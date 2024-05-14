# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BOEOOC(Document):
	pass

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_unique_cargo_name(doctype, txt, searchfield, start, page_len, filters):
	vessel = filters.get("vessel")
	return frappe.get_all(
		"Vessel Details",
		parent_doctype="Vessel",
		filters={"parent": vessel},
		fields=["distinct item"],
		as_list=1,
	)

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_unique_customer_name(doctype, txt, searchfield, start, page_len, filters):
	vessel = filters.get("vessel")
	return frappe.get_all(
		"Vessel Details",
		parent_doctype="Vessel",
		filters={"parent": vessel},
		fields=["distinct customer_name"],
		as_list=1,
	)
