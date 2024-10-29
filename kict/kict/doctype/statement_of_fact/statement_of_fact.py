# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date,get_last_day,getdate,get_datetime,add_days
from frappe.utils.data import get_date_str
from kict.api import get_port_date

class StatementofFact(Document):
	def validate(self):
		self.validate_dates()
		if self.first_line_ashore and self.all_line_cast_off:
			self.set_berth_stay_hours()

	def validate_dates(self):
		if self.first_line_ashore and self.all_line_cast_off:
			if self.all_line_cast_off < self.first_line_ashore:
				frappe.throw(_("All line cast off cannot be less than first line ashore"))
			if self.vessel_given_readiness__for_sailing:
				if self.first_line_ashore > self.vessel_given_readiness__for_sailing:
					frappe.throw(_("First line ashore can not be greater than vessel given readiness for sailing"))
				# if self.vessel_given_readiness__for_sailing > self.all_line_cast_off:
				# 	frappe.throw(_("Vessel given readiness for sailing can not be greater than all line cast off"))

	@frappe.whitelist()
	def set_berth_stay_hours(self):
			# vessel given readiness related logic
			# 1) if no value is given
			# 2) if vessel given readiness is greater than the All line Cast off
			# 3)  diff_of_all_line_and_readiness  < 4
			# 4)  diff_of_all_line_and_readiness  > 4 and vessel_delay_account_row is NOT present
			# for the above four cases
			# stay hours = all line cast off - first line ashore			
			# if not self.vessel_given_readiness__for_sailing:
			# 	c_all_line_cast_off=self.all_line_cast_off
			# #  Round Up [ First Line Ashore - ( All Line Cast Off - Vessel given readiness - vessel delay due to terminal account ) ]
			# elif self.vessel_given_readiness__for_sailing:
			# 	if self.vessel_given_readiness__for_sailing > self.all_line_cast_off :
			# 		c_all_line_cast_off=self.all_line_cast_off
			# 	else:
			# 		diff_of_all_line_and_readiness = frappe.utils.time_diff_in_hours(self.all_line_cast_off,self.vessel_given_readiness__for_sailing)
			# 		if diff_of_all_line_and_readiness > 4 :
			# 			vessel_delay_account_for_terminal = frappe.db.get_single_value('Coal Settings', 'vessel_delay_account_for_terminal')
			# 			if vessel_delay_account_for_terminal:
			# 				vessel_delay_account_row=frappe.db.get_list('Vessel Delay Details',parent_doctype='Vessel Delay', 
			# 										filters={'parent':self.vessel,'account_delays':vessel_delay_account_for_terminal},
			# 										fields=['total_hours'])
			# 				print(vessel_delay_account_row)
			# 				if len(vessel_delay_account_row)>0:
			# 					vessel_delay_time=vessel_delay_account_row[0].total_hours/3600
			# 					int_delay_hours, delay_dec_sec = divmod(vessel_delay_time, 1)
			# 					print(int_delay_hours,"-->int_delay_hours",delay_dec_sec,"-->delay_dec_sec")
			# 					if delay_dec_sec>0:
			# 						int_delay_hours = int_delay_hours + 1
			# 					c_all_line_cast_off=add_to_date(self.all_line_cast_off, hours=-int_delay_hours)
			# 				else:
			# 					c_all_line_cast_off	= self.all_line_cast_off
			# 		else:
			# 			print("condition 3")
			# 			c_all_line_cast_off = self.all_line_cast_off

			# # common logic 
			# berth_stay_seconds=frappe.utils.time_diff_in_seconds(c_all_line_cast_off,self.first_line_ashore)
			# print('berth_stay_seconds',berth_stay_seconds)
			# berth_stay_hours_in_decimal=(berth_stay_seconds/3600)
			# int_hours, dec_sec = divmod(berth_stay_hours_in_decimal, 1)
			# if dec_sec>0:
			# 	int_hours=int_hours+1
			# berth_stay_hours=int_hours
			# self.vessel_stay_hours = berth_stay_hours
			# month_end_date = get_last_day(self.first_line_ashore)
			
			# # convert month_end_date to port date, because royalty is paid to port
			# month_end_date_with_time=get_datetime(get_date_str(add_days(month_end_date,1))+' 06:00:00')
			
			# if get_datetime(self.all_line_cast_off) > month_end_date_with_time:
			# 	current_month_stay_seconds=frappe.utils.time_diff_in_seconds(month_end_date_with_time,self.first_line_ashore)
			# 	current_month_stay_hours_in_decimal=(current_month_stay_seconds/3600)
			# 	current_month_int_hours, current_month_dec_sec = divmod(current_month_stay_hours_in_decimal, 1)
			# 	if current_month_dec_sec>0:
			# 		current_month_int_hours=current_month_int_hours+1				
			# 	self.current_month_stay_hours=current_month_int_hours
			# 	self.next_month_stay_hours=self.vessel_stay_hours-self.current_month_stay_hours
			# else:
			# 	self.current_month_stay_hours=self.vessel_stay_hours
			# 	self.next_month_stay_hours=0

			total_vessel_delay = 0
			vessel_delay = frappe.db.get_all("Vessel Delay Details",
									filters={"parent":self.name,"to_exempt_from_berth_hours":1},
									fields=["account_delays","total_hours"])
			if len(vessel_delay)>0:
				for row in vessel_delay:
					total_vessel_delay = total_vessel_delay + row.total_hours

			if self.vessel_given_readiness__for_sailing:
				diff_of_all_line_and_readiness = frappe.utils.time_diff_in_hours(self.all_line_cast_off,self.vessel_given_readiness__for_sailing)

				if diff_of_all_line_and_readiness < 4:
					diff_of_first_line_and_all_line = frappe.utils.time_diff_in_seconds(self.all_line_cast_off,self.first_line_ashore)
					stay_hours = diff_of_first_line_and_all_line - total_vessel_delay
					stay_int_hours, stay_dec_seconds = divmod(stay_hours/3600, 1)
					if stay_dec_seconds > 0:
						stay_int_hours = stay_int_hours + 1
					self.vessel_stay_hours = stay_int_hours

				elif diff_of_all_line_and_readiness >= 4 and self.is_delay_due_to_vessel_customer == 1:
					diff_of_first_line_and_all_line = frappe.utils.time_diff_in_seconds(self.all_line_cast_off,self.first_line_ashore)
					stay_hours = diff_of_first_line_and_all_line - total_vessel_delay
					stay_int_hours, stay_dec_seconds = divmod(stay_hours/3600, 1)
					if stay_dec_seconds > 0:
						stay_int_hours = stay_int_hours + 1
					self.vessel_stay_hours = stay_int_hours

				elif diff_of_all_line_and_readiness >= 4:
					new_vessel_readiness = frappe.utils.add_to_date(self.vessel_given_readiness__for_sailing, hours=4)
					diff_of_first_line_and_readiness = frappe.utils.time_diff_in_seconds(new_vessel_readiness,self.first_line_ashore)
					stay_hours = diff_of_first_line_and_readiness - total_vessel_delay
					stay_int_hours, stay_dec_seconds = divmod(stay_hours/3600, 1)
					if stay_dec_seconds > 0:
						stay_int_hours = stay_int_hours + 1
					self.vessel_stay_hours = stay_int_hours
					
			else :
				diff_of_first_line_and_all_line = frappe.utils.time_diff_in_seconds(self.all_line_cast_off,self.first_line_ashore)
				stay_hours = diff_of_first_line_and_all_line - total_vessel_delay
				stay_int_hours, stay_dec_seconds = divmod(stay_hours/3600, 1)
				if stay_dec_seconds > 0:
					stay_int_hours = stay_int_hours + 1
				self.vessel_stay_hours = stay_int_hours

			month_end_date = get_last_day(self.first_line_ashore)
			
			# convert month_end_date to port date, because royalty is paid to port
			month_end_date_with_time=get_datetime(get_date_str(add_days(month_end_date,1))+' 06:00:00')
			
			if get_datetime(self.all_line_cast_off) > month_end_date_with_time:
				current_month_stay_seconds=frappe.utils.time_diff_in_seconds(month_end_date_with_time,self.first_line_ashore)
				current_month_stay_hours_in_decimal=(current_month_stay_seconds/3600)
				current_month_int_hours, current_month_dec_sec = divmod(current_month_stay_hours_in_decimal, 1)
				if current_month_dec_sec>0:
					current_month_int_hours=current_month_int_hours+1				
				self.current_month_stay_hours=current_month_int_hours
				self.next_month_stay_hours=self.vessel_stay_hours-self.current_month_stay_hours
			else:
				self.current_month_stay_hours=self.vessel_stay_hours
				self.next_month_stay_hours=0