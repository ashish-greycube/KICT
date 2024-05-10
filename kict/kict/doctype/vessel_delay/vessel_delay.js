// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Vessel Delay", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Vessel Delay Details",{
    delay_start_time(frm,cdt,cdn){
        set_total_hours(frm,cdt,cdn)
    }
    ,
    delay_end_time(frm,cdt,cdn){
        set_total_hours(frm,cdt,cdn)
    }
})

let set_total_hours = function(frm,cdt,cdn){
    let row = locals[cdt][cdn]
    if(row.delay_end_time && row.delay_start_time){
        let time_diff_in_seconds = moment(row.delay_end_time).diff(row.delay_start_time, 'seconds', true);
        frappe.model.set_value(cdt, cdn, 'total_hours', time_diff_in_seconds);
    }
}
