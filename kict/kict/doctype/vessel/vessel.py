# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Vessel(Document):
	
	def validate(self):
		self.set_total_tonnage()
		self.set_unique_bl_no()

	def set_total_tonnage(self):
		total_tonnage = 0
		for row in self.get("vessel_details"):
			if row.tonnage_mt:
				total_tonnage = total_tonnage + row.tonnage_mt

		self.total_tonnage_mt = total_tonnage

	def set_unique_bl_no(self):
		vessel_details = self.get("vessel_details")
		for row in vessel_details:
			if row.bl_order_ref_no:
				pass
			else:
				row.bl_order_ref_no = vessel_details[vessel_details.index(row)].name