# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _ 


class RakeDispatch(Document):
	def validate(self):
		self.validate_silo_qty()

	def validate_silo_qty(self):
		# railway_item_detail = self.get("plotwise_silo_qty_detail")
		# if len(railway_item_detail) > 0:
			
		# 	for row in railway_item_detail:
		# 		total_silo_qty = 0
		# 		if row.get("silo_qty") == 0:
		# 			frappe.throw(_("Row #{0} : RR Item Weight cannot be 0").format(row.idx))
		# 		for ele in railway_item_detail:
		# 			if row.vessel == ele.vessel and row.item == ele.item:
		# 				total_silo_qty = total_silo_qty + ele.silo_qty
		# 		rr_vessel_name = row.vessel
		# 		rr_vessel_item_name = row.item
		# 		vessel_detail = frappe.db.get_all("Vessel Details", 
		# 					parent_doctype='Vessel',
		# 					filters={"parent": rr_vessel_name,"item":rr_vessel_item_name}, 
		# 					fields=["tonnage_mt"])
		# 		if total_silo_qty > vessel_detail[0].tonnage_mt:
		# 			frappe.throw(_("Oty {0} for {1} cannot be greater than {2}.").format(total_silo_qty,rr_vessel_item_name,vessel_detail[0].tonnage_mt))
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

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_unique_customer_item_list(doctype, txt, searchfield, start, page_len, filters):
	vcn_no = filters.get("vessel_name")
	return frappe.get_all(
		"Vessel Details",
		parent_doctype="Vessel",
		filters={"parent": vcn_no},
		fields=["item"],
		as_list=1,
	)