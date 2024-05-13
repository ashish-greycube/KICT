# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document


class HourlyOperations(Document):
	def validate(self):
		self.set_day_tonnage_and_running_total()
		self.set_balance()
	
	def set_day_tonnage_and_running_total(self):
		ho_details = self.get("hourly_operation_details")
		if len(ho_details) > 0:
			for row in ho_details:
				if row.hourly_receipt_qty:
					if ho_details.index(row) == 0:
						row.period_tonnage_running_total = row.hourly_receipt_qty
						row.day_tonnage = self.total_tonnage_mt - row.period_tonnage_running_total
					else :
						row.period_tonnage_running_total = row.hourly_receipt_qty + ho_details[ho_details.index(row)-1].period_tonnage_running_total
						row.day_tonnage = ho_details[ho_details.index(row)-1].day_tonnage - row.hourly_receipt_qty

	def set_balance(self):
		ho_details = self.get("hourly_operation_details")
		length = len(ho_details)
		if len(ho_details) > 0:
			if ho_details[length-1].period_tonnage_running_total:
				balance = self.total_tonnage_mt - ho_details[length-1].period_tonnage_running_total
				self.balance = balance