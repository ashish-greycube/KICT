# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class EmployeeFooding(Document):
	def validate(self):
		self.validate_meal_price()
		self.calculate_borne_by_company_and_employee()

	def validate_meal_price(self):
		if self.meal_price == None:
			frappe.throw(_("Please set meal price"))

	def calculate_borne_by_company_and_employee(self):
		if self.meal_price:
			meal_price = self.meal_price
			percentage_borne_by_company = frappe.db.get_single_value("Coal Settings","food_borne_by_company")
			borne_by_company = meal_price * (percentage_borne_by_company / 100)
			borne_by_employee = meal_price - borne_by_company
			self.borne_by_company = borne_by_company
			self.borne_by_employee = borne_by_employee

@frappe.whitelist()
def get_meal_price(meal_type):
	meal_price_list = frappe.db.get_single_value("Coal Settings","food_meal_price_list")
	from erpnext.stock.get_item_details import get_price_list_rate_for
	args=frappe._dict({
		'price_list':meal_price_list,
		'qty':1,
		'uom':frappe.db.get_value('Item', meal_type, 'stock_uom')})
	return get_price_list_rate_for(args,meal_type)		


