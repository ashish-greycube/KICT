frappe.ui.form.on('Customer', {
    setup(frm) {
        frappe.db.get_single_value('Coal Settings', 'storage_charges_item_group')
        .then(storage_charges_item_group => {
            console.log('storage_charges_item_group',storage_charges_item_group)
            frm.set_query("item", "custom_chargeable_storage_charges_slots_details", function (doc, cdt, cdn) {
                return {
                    filters: {
                        item_group: ["=", storage_charges_item_group],
                    },
                };

            })
        })
    },
})