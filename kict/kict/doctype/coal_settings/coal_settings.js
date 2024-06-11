// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Coal Settings", {
    refresh: function(frm){
        if (frm.is_dirty()==false){
            frm.add_custom_button(__('Create Royalty Invoice'), () => create_purchase_invoice_for_royalty_charges(frm), __("Create"));
        }
    
    }
});

function create_purchase_invoice_for_royalty_charges(frm) {
    console.log("dialog")

    let dialog = undefined
    const dialog_field = [
        {
            fieldtype: "Link",
            fieldname: "supplier_name_field",
            label: __("Supplier Name"),
            options: "Supplier",
            reqd: 1
        },
        {
            fieldtype: "Data",
            fieldname: "supplier_invoice_no_field",
            label: __("Supplier Invoice no"),
            reqd: 1
        },
        {
            fieldtype: "Date",
            fieldname: "posting_date_field",
            label: __("Posting Date"),
            reqd: 1
        }
    ]

    dialog = new frappe.ui.Dialog({
        title: __("Enter Details for Royalty Charges"),
        fields: dialog_field,
        primary_action_label: 'Create Purchase Invoice',
        primary_action: function (values) {
            console.log(values,'va')
            frappe.call({
                method: "kict.api.create_purchase_invoice_for_royalty_charges",
                args: {
                    "source_name": undefined,
                    "target_doc": undefined,
                    "supplier_name":values.supplier_name_field,
                    "supplier_invoice_no":values.supplier_invoice_no_field,
                    "posting_date":values.posting_date_field,
                },
                callback: function (response) {
                    if (response.message) {
                        let url_list = '<a href="/app/purchase-invoice/' + response.message + '" target="_blank">' + response.message + '</a><br>'
                        frappe.show_alert({
                            title: __('Sales Order is created'),
                            message: __(url_list),
                            indicator: 'green'
                        }, 12);
                        window.open(`/app/purchase-invoice/` + response.message);
                    }
                }
            });
            dialog.hide()
        }
    });
    dialog.show()
}