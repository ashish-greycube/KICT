// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Rake Delay", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Rake Delay Reason", {
    to_delay(frm,cdt,cdn){
        set_total_time(frm,cdt,cdn)
    },
    from_delay(frm,cdt,cdn){
        set_total_time(frm,cdt,cdn)
    }
})

let set_total_time = function(frm,cdt,cdn){
    let row = locals[cdt][cdn]
    if(row.from_delay && row.to_delay){
        let time_diff_in_seconds = moment(row.to_delay).diff(row.from_delay, 'seconds', true);
        frappe.model.set_value(cdt, cdn, 'total', time_diff_in_seconds);
    }
}