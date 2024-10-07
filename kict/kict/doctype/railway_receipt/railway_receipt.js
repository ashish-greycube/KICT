// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Railway Receipt", {
    setup(frm) {
        frm.set_query("item", "railway_receipt_item_details", function (doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (row.vessel) {
                return {
                    query: "kict.kict.doctype.railway_receipt.railway_receipt.get_unique_customer_item_list",
                    filters: {
                        vessel_name: row.vessel
                    },
                };
            }
        });

        frm.set_query("commercial_destination_item", "railway_receipt_item_details", function (doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            return {
                query: "kict.kict.doctype.railway_receipt.railway_receipt.get_unique_customer_item_list",
                filters: {
                    vessel_name: row.vessel,
                    is_customer_provided_item: 1
                },
            };
        });
    },
    onload(frm) {
        frm.trigger('railway_receipt_on_refresh_load')
    },
	refresh(frm) {
        frm.trigger('railway_receipt_on_refresh_load')
	},

    railway_receipt_on_refresh_load: function(frm){
        rr_item_details = frm.doc.railway_receipt_item_details
        delivery_note_created = true
        for(ele of rr_item_details){
            if(ele.is_dn_created == 'No'){
                delivery_note_created = false
            }
        }
        if (frm.doc.docstatus == 1 && delivery_note_created == false) {
            frm.add_custom_button(__('Delivery Note'), () => create_delivery_note_from_railway_receipt(frm), __("Create"));
        }
    }
});

function create_delivery_note_from_railway_receipt(frm){
    if (frm.is_dirty()==true) {
        frappe.throw({
            message: __("Please save the form to proceed..."),
            indicator: "red",
        });       
    }

    frappe.call({
        method: "kict.kict.doctype.railway_receipt.railway_receipt.create_delivery_note_from_railway_receipt",
        args: {
            "docname": frm.doc.name
        },
        callback: function (response) {
        }
    });

}
