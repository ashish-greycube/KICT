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
        if ((row.customer_name) && (row.commercial_destination_customer == undefined || row.commercial_destination_customer == "")){
            console.log("worked")
            frappe.model.set_value(cdt, cdn, 'commercial_destination_customer', row.customer_name);
        }
    },
    item(frm, cdt, cdn){
        let row = locals[cdt][cdn]
        if ((row.item) && (row.commercial_destination_item == undefined || row.commercial_destination_item == "")){
            console.log("worked")
            frappe.model.set_value(cdt, cdn, 'commercial_destination_item', row.item);
        }
    },
    no_of_wagons_loaded(frm, cdt, cdn){
        set_no_of_wagons_reject(frm, cdt, cdn)
    },
    no_of_wagons_placed(frm, cdt, cdn){
        set_no_of_wagons_reject(frm, cdt, cdn)
    },
    no_of_wagon_rejected_by_railway(frm, cdt, cdn){
        set_total_rejected_wagons(frm, cdt, cdn)
    },
    no_of_wagon_rejected_due_to_foreign_material(frm, cdt, cdn){
        set_total_rejected_wagons(frm, cdt, cdn)
    },

})

let set_no_of_wagons_reject = function (frm, cdt, cdn) {
    let row = locals[cdt][cdn]
    let reject_wagons = row.no_of_wagons_placed - row.no_of_wagons_loaded
    if (reject_wagons < 0){
        frappe.throw(__("Row {0}: No of wagons reject cannot be negative",[row.idx]))
    }
    frappe.model.set_value(cdt, cdn, 'no_of_wagons_reject', reject_wagons);

}

let set_total_rejected_wagons = function(frm, cdt, cdn) {
    let row = locals[cdt][cdn]
    let total_rejected_wagons = row.no_of_wagon_rejected_by_railway + row.no_of_wagon_rejected_due_to_foreign_material
    if (total_rejected_wagons < 0){
        frappe.throw(__("Row {0}: No of wagons reject cannot be negative",[row.idx]))
    }
    frappe.model.set_value(cdt, cdn, 'total_reject_wagon', total_rejected_wagons);
}