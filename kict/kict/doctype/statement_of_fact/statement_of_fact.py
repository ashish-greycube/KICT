# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date


class StatementofFact(Document):
	def validate(self):
		self.set_berth_stay_hours()

	def set_berth_stay_hours(self):
		if self.first_line_ashore and self.all_line_cast_off:
			if self.all_line_cast_off < self.first_line_ashore:
				frappe.throw(_("All Line Cast Off cannot be less than First Line Ashore"))
			if self.vessel_given_readiness__for_sailing:
				if self.first_line_ashore > self.vessel_given_readiness__for_sailing:
					frappe.throw(_("First Line Ashore can not be greater than Vessel Given Readiness for Sailing"))
				if self.vessel_given_readiness__for_sailing > self.all_line_cast_off:
					frappe.throw(_("Vessel Given Readiness for Sailing can not be greater than All Line Cast Off"))
			all_line_cast_off = self.all_line_cast_off
			if self.vessel_given_readiness__for_sailing:
				diff_of_all_line_and_readiness = frappe.utils.time_diff_in_hours(all_line_cast_off,self.vessel_given_readiness__for_sailing)
				if diff_of_all_line_and_readiness > 4 :
					all_line_cast_off = add_to_date(self.vessel_given_readiness__for_sailing, hours=4)
			
			berth_stay_seconds=frappe.utils.time_diff_in_seconds(all_line_cast_off,self.first_line_ashore)
			berth_stay_hours_in_decimal=(berth_stay_seconds/3600)
			int_hours, dec_sec = divmod(berth_stay_hours_in_decimal, 1)
			if dec_sec>0:
				int_hours=int_hours+1
			
			berth_stay_hours=int_hours
			self.vessel_stay_hours = berth_stay_hours
				
