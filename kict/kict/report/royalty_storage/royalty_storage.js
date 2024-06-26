// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt


frappe.query_reports["Royalty Storage"] = {
	// Filter----Vessel From Date : first_line_ashore To Date : today CustomerItem Batch
	"filters": [
		{
			"fieldname": "vessel",
			"label":__("Vessel"),
			"fieldtype": "Link",
			"options": "Vessel",
			"reqd":1,
		 	 on_change: function () {
				let vessel = frappe.query_report.get_filter_value("vessel");
				frappe.db.get_value('Statement of Fact', vessel, 'first_line_ashore')
				.then(r => {
					let values = r.message;
					frappe.query_report.set_filter_value("from_date", values.first_line_ashore);
		
				})

		 }
		},
		{
			"fieldname": "from_date",
			"label":__("From Date"),
			"fieldtype": "Date",
			"width": "40px",
			"read_only":1
		},
		{
			"fieldname": "to_date",
			"label":__("To Date"),
			"fieldtype": "Date",
			// "width": "40px",
            "default": frappe.datetime.month_end()
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
		{
			"fieldname": "only_for_royalty",
			"label":__("Only for Royalty"),
			"fieldtype": "Check",
			"default": 1,
			"read_only":1
		},		

	]
};

