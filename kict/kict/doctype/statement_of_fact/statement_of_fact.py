# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date,get_last_day,getdate,get_datetime
from frappe.utils.data import get_date_str

class StatementofFact(Document):
	def validate(self):
		self.validate_dates()
		self.set_berth_stay_hours()

	def validate_dates(self):
		if self.first_line_ashore and self.all_line_cast_off:
			if self.all_line_cast_off < self.first_line_ashore:
				frappe.throw(_("All line cast off cannot be less than first line ashore"))
			if self.vessel_given_readiness__for_sailing:
				if self.first_line_ashore > self.vessel_given_readiness__for_sailing:
					frappe.throw(_("First line ashore can not be greater than vessel given readiness for sailing"))
				if self.vessel_given_readiness__for_sailing > self.all_line_cast_off:
					frappe.throw(_("Vessel given readiness for sailing can not be greater than all line cast off"))

	def set_berth_stay_hours(self):
			if not self.vessel_given_readiness__for_sailing:
				self.vessel_stay_hours=0
				return



			
			#  Round Up [ First Line Ashore - ( All Line Cast Off - Vessel given readiness - vessel delay due to terminal account ) ]
			if self.vessel_given_readiness__for_sailing:
				diff_of_all_line_and_readiness = frappe.utils.time_diff_in_hours(all_line_cast_off,self.vessel_given_readiness__for_sailing)
				
				if diff_of_all_line_and_readiness > 4 :
					vessel_delay_account_for_terminal = frappe.db.get_single_value('Coal Settings', 'vessel_delay_account_for_terminal')
					if vessel_delay_account_for_terminal:
						vessel_delay_account_row=frappe.db.get_list('Vessel Delay Details',parent_doctype='Vessel Delay', 
												  filters={'parent':self.vessel,'type_of_delays':vessel_delay_account_for_terminal},
												  fields=['delay_end_time'])
						if len(vessel_delay_account_row)>0:
							vessel_delay_end_time=vessel_delay_account_row[0].delay_end_time
							c_all_line_cast_off=vessel_delay_end_time

						else:
							c_all_line_cast_off	= self.all_line_cast_off

					
					all_line_cast_off = add_to_date(self.vessel_given_readiness__for_sailing, hours=4)

				else:
					c_all_line_cast_off = self.all_line_cast_off
			
			
			
			
			berth_stay_seconds=frappe.utils.time_diff_in_seconds(c_all_line_cast_off,self.first_line_ashore)
			print('berth_stay_seconds',berth_stay_seconds)
			berth_stay_hours_in_decimal=(berth_stay_seconds/3600)
			int_hours, dec_sec = divmod(berth_stay_hours_in_decimal, 1)
			print('dec_sec',dec_sec)
			if dec_sec>0:
				int_hours=int_hours+1
			berth_stay_hours=int_hours
			self.vessel_stay_hours = berth_stay_hours

			month_end_date = get_last_day(self.first_line_ashore)
			month_end_date_with_time=get_datetime(get_date_str(month_end_date)+' 23:59:59')
			
			if get_datetime(self.all_line_cast_off) > month_end_date_with_time:
				print('go next')
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

				
