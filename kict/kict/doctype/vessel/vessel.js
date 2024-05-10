// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vessel", {
    onload(frm) {
        frm.set_query("commodity", "vessel_details", function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {
                filters: {
                    is_stock_item: 1,
                    is_customer_provided_item: 1,
                    customer: d.customer_name
                },
            };
        })
    }
});

frappe.ui.form.on("Vessel Details", {
    tonnage_mt(frm, cdt, cdn) {
        total_tonnage_of_vessel(frm, cdt, cdn)
    },
    vessel_details_remove: function (frm, cdt, cdn) {
        total_tonnage_of_vessel(frm, cdt, cdn)
    }
})

let total_tonnage_of_vessel = function (frm, cdt, cdn) {
    let total_tonnage = 0
    frm.doc.vessel_details.forEach(function (item) {
        total_tonnage = total_tonnage + item.tonnage_mt
    })
    frm.set_value("total_tonnage_mt", total_tonnage)
}