frappe.ui.form.on('Customer', {
    customer_group: function (frm) {
        set_required_for_cargo_charges(frm)
    },
    custom_storage_charge_based_on: function (frm) {
        set_required_for_custom_storage_charge_based_on_table(frm) 
    },
    setup(frm) {
        frappe.db.get_value('Coal Settings', 'Coal Settings', ['storage_charges_16_25_days', 'storage_charges_beyond_26_days'])
        .then(r => {
            let values = r.message;
            let item_require = []
            if (values){
                item_require.push(values.storage_charges_16_25_days)
                item_require.push(values.storage_charges_beyond_26_days)
            }
            console.log(item_require)
            frm.set_query("item", "custom_chargeable_storage_charges_slots_details", function (doc, cdt, cdn) {
                return {
                    filters: {
                        // item_code: item_code,
                        name: ["in", item_require],
                    },
                };

            })
        })
        frm.set_query("item", "custom_chargeable_storage_charges_slots_details", function (doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            return {
                query: "kict.api.get_item_from_coal_settings",
                filters: {
                    vessel_name: row.vcn_no
                },
            };
        });
        set_required_for_cargo_charges(frm)
    },
})

function set_required_for_cargo_charges(frm) {
    frappe.db.get_single_value('Coal Settings','customer_group_for_cargo_customer')
        .then(r => {
            console.log(r)
            if (frm.doc.customer_group == r) {
                frm.set_df_property('custom_cargo_handling_charges_slots_details','reqd',1)
                frm.set_df_property('custom_storage_charge_based_on','reqd',1)
                // frm.set_df_property('custom_chargeable_storage_charges_slots_details','reqd',1)
                // frm.set_df_property('custom_free_storage_days','reqd',1)
                set_required_for_custom_storage_charge_based_on_table(frm)
            }else{
                frm.set_df_property('custom_cargo_handling_charges_slots_details','reqd',0)
                frm.set_df_property('custom_storage_charge_based_on','reqd',0)
                // frm.set_df_property('custom_chargeable_storage_charges_slots_details','reqd',0)
                // frm.set_df_property('custom_free_storage_days','reqd',0)  
            }
        })
}

function set_required_for_custom_storage_charge_based_on_table(frm) {
    if (frm.doc.custom_storage_charge_based_on == 'Fixed Days'){
        frm.set_df_property('custom_no_of_days','reqd',1)
    }else{
        frm.set_df_property('custom_no_of_days','reqd',0)
    }
    if (frm.doc.custom_storage_charge_based_on == 'Actual Storage Days') {
        frm.set_df_property('custom_chargeable_storage_charges_slots_details','reqd',1)
    } else {
        frm.set_df_property('custom_chargeable_storage_charges_slots_details','reqd',0)
    }
}