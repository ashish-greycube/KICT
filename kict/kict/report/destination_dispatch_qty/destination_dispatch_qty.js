// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt
frappe.query_reports["Destination Dispatch Qty"] = {
	"filters": [
		{
			"fieldname": "customer",
			"label":__("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
	]
};
