# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VesselDelay(Document):
	def validate(self):
			self.set_total_hours()
			self.set_total_delay_hours()
		
	def set_total_hours(self):  
		for row in self.get("vessel_delay_details"):
			if row.delay_start_time and row.delay_end_time:
				end_date = row.delay_end_time
				start_date = row.delay_start_time
				diff=frappe.utils.time_diff_in_seconds(end_date,start_date)
				row.total_hours = diff

	def set_total_delay_hours(self):
			total_delay_hours = 0
			for row in self.get("vessel_delay_details"):
				total_delay_hours = total_delay_hours + row.total_hours
			print(total_delay_hours,"  total_delay_hours")
			self.vessel_total_delay_hours = total_delay_hours				