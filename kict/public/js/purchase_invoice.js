frappe.ui.form.on('Purchase Invoice', {
    "custom_is_royalty_invoice":function(frm) {
        if (frm.is_new()==1 && frm.doc.items.length==1 && frm.doc.items[0].item_code==undefined) {
            frappe.db.get_single_value('Coal Settings', 'birth_hire_item_for_coastal_vessel')
            .then(birth_hire_item_for_coastal_vessel => {
                frappe.model.set_value(frm.doc.items[0].doctype, frm.doc.items[0].name, "item_code", birth_hire_item_for_coastal_vessel);
            })
        }
    },
    onload: function(frm){
        if (frm.is_new()==1){
            frm.add_custom_button(__('Create Royalty Invoice'), () => create_purchase_invoice_for_royalty_charges(frm), __("Create"));
            console.log("new")
        }
    
    }
})

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
            frappe.call({
                method: "kict.api.create_purchase_invoice_for_royalty_charges",
                args: {
                    // "source_name": frm.doc.name,
                    "target_doc": undefined,
                    "supplier_name":values.supplier_name_field,
                    "supplier_invoice_no":values.supplier_invoice_no_field,
                    "posting_date":values.posting_date_field,
                },
                callback: function (response) {
                    console.log(response.message)
                }
            });
            dialog.hide()
        }
    });
    dialog.show()
}