// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Hatch wise", {

    onload(frm) {
        frm.trigger("grade_filter")
    },
    vessel(frm) {
        frm.trigger("grade_filter")
    },
    grade_filter: function (frm) {
        frappe.db.get_list("Vessel Details", {
            parent_doctype: "Vessel",
            filters: {
                "parent": frm.doc.vessel
            },
            fields: ["grade"]
        }).then(records => {
            let cargo = records
            let grade = []
            cargo.forEach(r => {
                grade.push(r.grade)
            })
            let unique_grade = [...new Set(grade)]
            frm.set_query("cargo_grade", "hatch_wise_details", function () {
                let return_filters = {}
                if (frm.doc.vessel) {
                    return_filters["name"] = ["in", unique_grade]
                }
                else {
                    return_filters["name"] = ["in", '']
                }
                return {
                    filters: return_filters
                }
            });
        })
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