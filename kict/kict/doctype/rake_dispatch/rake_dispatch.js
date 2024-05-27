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
    },
});