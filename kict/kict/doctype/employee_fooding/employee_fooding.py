# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form

class EmployeeFooding(Document):
	def validate(self):
		self.validate_meal_price()
		self.calculate_borne_by_company_and_employee()
		self.validate_unique_employee_fooding()

	def validate_meal_price(self):
		if self.meal_price == None:
			frappe.throw(_("Please set meal price"))

	def calculate_borne_by_company_and_employee(self):
		if self.meal_price:
			meal_price = self.meal_price
			is_meal_subsidised = frappe.db.get_value("Item",self.meal_type,"custom_is_subsidised")
			if is_meal_subsidised == 1:
				percentage_borne_by_company = frappe.db.get_single_value("Coal Settings","food_borne_by_company")
				borne_by_company = meal_price * (percentage_borne_by_company / 100)
				borne_by_employee = meal_price - borne_by_company
				self.borne_by_company = borne_by_company
				self.borne_by_employee = borne_by_employee
			elif is_meal_subsidised == 0:
				self.borne_by_employee = meal_price
				self.borne_by_company = 0

	def validate_unique_employee_fooding(self):
		prev_list = frappe.db.get_all('Employee Fooding', 
								filters={'employee': self.employee, 'meal_date': self.meal_date, 'meal_type': self.meal_type, 'name': ['!=', self.name]},
								fields=['name'])
		
		if len(prev_list) > 0:
			frappe.throw(_('This Employee Fooding is already exist - {0}.'
				  .format(get_link_to_form('Employee Fooding', prev_list[0].name))))

@frappe.whitelist()
def get_meal_price(meal_type):
	meal_price_list = frappe.db.get_single_value("Coal Settings","food_meal_price_list")
	from erpnext.stock.get_item_details import get_price_list_rate_for
	args=frappe._dict({
		'price_list':meal_price_list,
		'qty':1,
		'uom':frappe.db.get_value('Item', meal_type, 'stock_uom')})
	return get_price_list_rate_for(args,meal_type)		


