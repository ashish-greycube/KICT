# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RakeDelay(Document):
	def validate(self):
		self.set_total_dutation()

	def set_total_dutation(self):
		for row in self.get("rake_delay_reason"):
			if row.from_delay and row.to_delay:
				end_date = row.to_delay
				start_date = row.from_delay
				diff=frappe.utils.time_diff_in_seconds(end_date,start_date)
				row.total_hours = diff
		
		
