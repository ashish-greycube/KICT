// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Equipemnts In and Out", {
    setup(frm) {
        frm.set_query("commodity_code", function () {
            if (frm.doc.vessel) {
                return {
                    query: "kict.kict.doctype.equipemnts_in_and_out.equipemnts_in_and_out.get_unique_commodity",
                    filters: {
                        vessel: frm.doc.vessel
                    },
                };
            }
        });
    },
    get_all_fast(frm) {
        frappe.db.get_list("SOF Details", {
            parent_doctype: "Statement of Fact",
            filters: {
                parent: frm.doc.vessel
            },
            fields: ["vessel_made_all_fast"]
        }).then(records => {
            if (records.length > 0) {
                frm.set_value("all_fast", records[0].vessel_made_all_fast)
            }
            else {
                frm.set_value("all_fast",)
            }
        })
    }
});

frappe.ui.form.on("Equipemnts In and Out Details", {
    equipment_in_date_time(frm, cdt, cdn) {
        set_total_engaged_time(frm, cdt, cdn)
    },
    equipment_out_date_time(frm, cdt, cdn) {
        set_total_engaged_time(frm, cdt, cdn)
    }
})

let set_total_engaged_time = function (frm, cdt, cdn) {
    let row = locals[cdt][cdn]
    if (row.equipment_in_date_time && row.equipment_out_date_time) {
        let time_diff_in_seconds = moment(row.equipment_out_date_time).diff(row.equipment_in_date_time, 'seconds', true);
        frappe.model.set_value(cdt, cdn, 'total_engaged_time', time_diff_in_seconds);
    }
}
