// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt


frappe.query_reports["Storage Charges"] = {
	// Filter----Vessel From Date : first_line_ashore To Date : today CustomerItem Batch
	"filters": [
		{
			"fieldname": "vessel",
			"label":__("Vessel"),
			"fieldtype": "Link",
			"options": "Vessel",
		},
		{
			"fieldname": "from_date",
			"label":__("From Date"),
			"fieldtype": "Date",
		},
		{
			"fieldname": "to_date",
			"label":__("To Date"),
			"fieldtype": "Date",
            "default": frappe.datetime.nowdate()
		},
		{
			"fieldname": "customer_item",
			"label":__("Customer Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "batch_no",
			"label":__("Batch No"),
			"fieldtype": "Link",
			"options": "Batch",
		},

	]
};
