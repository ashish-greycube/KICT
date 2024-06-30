// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Commercial Stock Balance"] = {
	"filters": [
		{
			"fieldname": "customer",
			"label":__("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
	]
};
