# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AgentsDO(Document):
	def validate(self):
		self.set_do_balance_qty()

	def set_do_balance_qty(self):
		agents_details = self.get("agents_do_detail")
		for row in agents_details:
			if row.do_received_qty:
				if row.idx == 1:
					row.do_balance_qty = self.total_tonnage_mt - row.do_received_qty
				else:
					row.do_balance_qty = agents_details[row.idx-2].do_balance_qty - row.do_received_qty
