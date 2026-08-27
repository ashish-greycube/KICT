frappe.ui.form.on('Purchase Invoice', {
    "custom_is_royalty_invoice":function(frm) {
        if (frm.is_new()==1 && frm.doc.items.length==1 && frm.doc.items[0].item_code==undefined) {
            frappe.db.get_single_value('Coal Settings', 'birth_hire_item_for_coastal_vessel')
            .then(birth_hire_item_for_coastal_vessel => {
                frappe.model.set_value(frm.doc.items[0].doctype, frm.doc.items[0].name, "item_code", birth_hire_item_for_coastal_vessel);
            })
        }
    },
})

frappe.ui.form.on('Purchase Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn]
        setTimeout(() => {
            if (frm.doc.custom_is_royalty_invoice == 1) {
                if (row.item_code != undefined || row.item_code != "") {
                    frappe.call({
                        method : "kict.api.apply_royalty_percentage",
                        args: {
                            item_code: row.item_code,
                            vessel : row.vessel,
                            posting_date : frm.doc.posting_date
                        },
                        callback: function(r) {
                            if (r.message) {
                            frappe.model.set_value(cdt, cdn, "rate", r.message)
                            }
                        }
                    })
                }
            }
        }, 500);
    },
})