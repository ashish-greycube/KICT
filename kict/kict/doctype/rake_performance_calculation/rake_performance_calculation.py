# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RakePerformanceCalculation(Document):
	def validate(self):
		self.set_punitive_charges()

	def set_punitive_charges(self):
		rcn_no = self.rcn
		punitive_charges = frappe.db.get_value("Railway Receipt",rcn_no,"total_punitive_amount")
		self.punitive_charges = punitive_charges
