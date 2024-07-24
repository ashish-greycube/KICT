// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rake Performance Calculation", {
	rcn(frm) {
        frappe.db.get_value("Railway Receipt",frm.doc.rcn,"total_punitive_amount")
        .then( r => 
            frm.set_value("punitive_charges",r.message.total_punitive_amount))
	},
});
