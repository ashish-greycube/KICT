// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Hatch wise", {

    setup(frm) {
        frm.set_query("cargo_grade", "hatch_wise_details", function () {
            if (frm.doc.vessel) {
                return {
                    query: "kict.kict.doctype.hatch_wise.hatch_wise.get_unique_grade_list",
                    filters: {
                        vessel: frm.doc.vessel
                    },
                };
            }
        });
        frm.set_query("coal_commodity", "hatch_wise_details", function () {
            if (frm.doc.vessel) {
                return {
                    query: "kict.kict.doctype.hatch_wise.hatch_wise.get_unique_coal_commodity_list",
                    filters: {
                        vessel: frm.doc.vessel
                    },
                };
            }
        });        
    }
});

frappe.ui.form.on("Hatch wise Details", {
    arrival_qty(frm, cdt, cdn) {
        set_balance_qty(frm, cdt, cdn)
    },
    discharged_qty(frm, cdt, cdn) {
        set_balance_qty(frm, cdt, cdn)
    },
    hatch(frm, cdt, cdn) {
        let details = frm.doc.hatch_wise_details
        let hatch = []
        for (ele of details) {
            if (ele.hatch) {
                if (!hatch.includes(ele.hatch)) {
                    hatch.push(ele.hatch)
                } else {
                    frappe.msgprint(__("Row {0}: You cannot select {1} again", [ele.idx, ele.hatch]))
                    frappe.model.set_value(cdt, cdn, "hatch",)
                }
            }
        }
    }
})

let set_balance_qty = function (frm, cdt, cdn) {
    let row = locals[cdt][cdn]
    let balance_qty = (row.arrival_qty || 0) - (row.discharged_qty || 0)
    frappe.model.set_value(cdt, cdn, "balance_qty", balance_qty)
    frm.refresh_field("hatch_wise_details")
}