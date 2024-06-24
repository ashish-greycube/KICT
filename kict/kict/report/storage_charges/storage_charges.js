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
			"reqd":1,
		 	 on_change: function () {
				let vessel = frappe.query_report.get_filter_value("vessel");
				frappe.db.get_value('Statement of Fact', vessel, 'first_line_ashore')
				.then(r => {
					let values = r.message;
					frappe.query_report.set_filter_value("from_date", values.first_line_ashore);
					
					frappe.call('kict.kict.report.storage_charges.storage_charges.get_unique_customer_to_set', {
						vessel: vessel
					}).then(r => {
						console.log(r.message)
						if (r.message) {
							frappe.query_report.set_filter_value("customer", r.message[0][0]);
						}
					})					
				})

		 }
		},
		{
			"fieldname": "customer",
			"label":__("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"reqd":1,
			get_query: function () {
				let vessel = frappe.query_report.get_filter_value("vessel");
				var filters = {
					vessel: vessel,
				};
				
				return {
					query: "kict.kict.report.storage_charges.storage_charges.get_unique_customer_list",
					filters: filters,
				};
			},	

		},		
		{
			"fieldname": "from_date",
			"label":__("From Date"),
			"fieldtype": "Date",
			"read_only":1
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
