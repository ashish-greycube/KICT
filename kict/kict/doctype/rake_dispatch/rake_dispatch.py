# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _ 
from frappe.utils import getdate,format_date


class RakeDispatch(Document):
	def validate(self):
		# self.validate_silo_qty()
		self.set_no_of_wagons_reject()
		self.validate_no_of_reject_wagons()

	def validate_silo_qty(self):
		railway_item_detail = self.get("plotwise_silo_qty_detail")
		if len(railway_item_detail) > 0:
			
			for row in railway_item_detail:
				total_silo_qty = 0
				if row.get("silo_qty") == 0:
					frappe.throw(_("Row #{0} : RR Item Weight cannot be 0").format(row.idx))
				for ele in railway_item_detail:
					if row.vessel == ele.vessel and row.item == ele.item:
						total_silo_qty = total_silo_qty + ele.silo_qty
				rr_vessel_name = row.vessel
				rr_vessel_item_name = row.item
				vessel_detail = frappe.db.get_all("Vessel Details", 
							parent_doctype='Vessel',
							filters={"parent": rr_vessel_name,"item":rr_vessel_item_name}, 
							fields=["tonnage_mt"])
				if total_silo_qty > vessel_detail[0].tonnage_mt:
					frappe.throw(_("Oty {0} for {1} cannot be greater than {2}.").format(total_silo_qty,rr_vessel_item_name,vessel_detail[0].tonnage_mt))

	def validate_no_of_reject_wagons(self):
		rake_dispatch_item = self.get("rake_prelim_entry")
		if len(rake_dispatch_item) > 0 :
			for row in rake_dispatch_item:
				rejected_wagons = row.no_of_wagons_reject
				calculated_rejected_wagons = (row.no_of_wagon_rejected_by_railway or 0) + (row.no_of_wagon_rejected_due_to_foreign_material or 0) + (row.no_of_wagon_rejected_due_to_others or 0)
				if rejected_wagons != calculated_rejected_wagons:
					frappe.throw(_("Row {0}: bifurcation of rejected wagons are not correct").format(row.idx))

	def before_naming(self):
		self.release_date=format_date(getdate(self.release_time))

	def set_no_of_wagons_reject(self):
		rake_dispatch_item = self.get("rake_prelim_entry")
		if len(rake_dispatch_item) > 0 :
			for row in rake_dispatch_item:
				row.no_of_wagons_reject = (row.no_of_wagons_placed or 0) - (row.no_of_wagons_loaded or 0)
				if (row.no_of_wagons_reject < 0):
					frappe.throw(_("Row {0}: No of wagons reject cannot be negative".format(row.idx)))

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
		fields=["distinct item"],
		as_list=1,
	)