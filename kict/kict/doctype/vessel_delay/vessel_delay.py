# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VesselDelay(Document):
	def validate(self):
			self.set_total_hours()
			self.set_total_delay_hours()
			self.validate_terminal_account()
		
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

	def validate_terminal_account(self):
		terminal_account_found = False
		terminal_account = frappe.db.get_single_value("Coal Settings","vessel_delay_account_for_terminal")
		for row in self.vessel_delay_details:
			if row.account_delays == terminal_account and terminal_account_found==False:
				terminal_account_found=True
			elif row.account_delays == terminal_account and terminal_account_found==True:
				frappe.throw(_("Row #{0}: You cannot select {1} account again.").format(row.idx,row.account_delays))			