# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
from frappe import _


class HourlyOperations(Document):
	def validate(self):
		self.set_day_tonnage_and_running_total()
		self.set_balance()
		self.set_discharged_commenced_and_completed_date_time()
		self.set_total_belt_weigher()
		self.set_total_grab_cycle()
	
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

	def set_discharged_commenced_and_completed_date_time(self):
		if self.discharge_commenced_date_time == None:
			frappe.throw(_("Please set discharge commenced in SOF"))
		if self.discharge_completed_date_time == None:
			frappe.throw(_("Please set discharge completed in SOF"))

	def set_total_belt_weigher(self):
		ho_details = self.get("hourly_operation_details")
		if len(ho_details) > 0:
			for row in ho_details:
				total_weigher = (row.a1_belt_weigher or 0) + (row.b1_belt_weigher or 0)
				print(total_weigher,"total belt",row.a1_belt_weigher,row.b1_belt_weigher)
				row.total_1a_1b = total_weigher

	def set_total_grab_cycle(self):
		ho_details = self.get("hourly_operation_details")
		if len(ho_details) > 0:
			for row in ho_details:
				total_grab_cycle = (row.sul_1_grab_cycle or 0) + (row.sul_2_grab_cycle or 0)
				print(total_grab_cycle,"total cycle",row.sul_1_grab_cycle,row.sul_2_grab_cycle)
				row.total_grab_cycle = total_grab_cycle