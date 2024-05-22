# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StatementofFact(Document):
	def validate(self):
		self.set_berth_stay_hours()

	def set_berth_stay_hours(self):
		if self.first_line_ashore and self.all_line_cast_off:
			diff=frappe.utils.time_diff_in_hours(self.all_line_cast_off,self.first_line_ashore)
			print(diff)
			self.vessel_stay_hours = diff
				
