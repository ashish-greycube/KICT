frappe.ui.form.on('Purchase Invoice', {
    "custom_is_royalty_invoice":function(frm) {
        if (frm.is_new()==1 && frm.doc.items.length==1 && frm.doc.items[0].item_code==undefined) {
            frappe.db.get_single_value('Coal Settings', 'birth_hire_item_for_coastal_vessel')
            .then(birth_hire_item_for_coastal_vessel => {
                frappe.model.set_value(frm.doc.items[0].doctype, frm.doc.items[0].name, "item_code", birth_hire_item_for_coastal_vessel);
            })
        }
    }
})