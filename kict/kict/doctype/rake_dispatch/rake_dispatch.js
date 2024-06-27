// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rake Dispatch", {
    setup(frm) {
        frm.set_query("grade", "rake_prelim_entry", function (doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (row.vcn_no) {
                return {
                    query: "kict.kict.doctype.rake_dispatch.rake_dispatch.get_unique_grade_list",
                    filters: {
                        vessel_name: row.vcn_no
                    },
                };
            }
        });

        frm.set_query("item", "rake_prelim_entry", function (doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (row.vcn_no) {
                return {
                    query: "kict.kict.doctype.rake_dispatch.rake_dispatch.get_unique_customer_item_list",
                    filters: {
                        vessel_name: row.vcn_no
                    },
                };
            }
        });

        frm.set_query("commercial_destination_item", "rake_prelim_entry", function (doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            return {
                query: "kict.kict.doctype.rake_dispatch.rake_dispatch.get_unique_customer_item_list",
                filters: {
                    vessel_name: row.vcn_no
                },
            };
        });
    },
});

frappe.ui.form.on("Rake Prelim Entry", {
    customer_name(frm, cdt, cdn){
        let row = locals[cdt][cdn]
        if ((row.customer_name) && (row.commercial_destination_customer == undefined || row.commercial_destination_customer == "") && (frm.is_new()==1)){
            console.log("worked")
            frappe.model.set_value(cdt, cdn, 'commercial_destination_customer', row.customer_name);
        }
    },
    item(frm, cdt, cdn){
        let row = locals[cdt][cdn]
        if ((row.item) && (row.commercial_destination_item == undefined || row.commercial_destination_item == "") && (frm.is_new()==1)){
            console.log("worked")
            frappe.model.set_value(cdt, cdn, 'commercial_destination_item', row.item);
        }
    }
})