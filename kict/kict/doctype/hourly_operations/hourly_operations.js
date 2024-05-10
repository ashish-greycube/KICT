// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Hourly Operations", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Hourly Operation Details", {
    hourly_receipt_qty(frm,cdt,cdn){
        set_running_total_and_day_tonnage(frm,cdt,cdn)
    },
    hourly_operation_details_remove(frm,cdt,cdn){
        set_running_total_and_day_tonnage(frm,cdt,cdn)
    },
    period_tonnage_running_total(frm,cdt,cdn){
        set_balance(frm,cdt,cdn)
    }
})

let set_running_total_and_day_tonnage = function(frm,cdt,cdn){
    let ho_details = frm.doc.hourly_operation_details
    let running_total = 0
    
    for (let index = 0; index < ho_details.length; index++) {
        if (index == 0) {
            frappe.model.set_value(ho_details[0].doctype, ho_details[0].name, "period_tonnage_running_total", ho_details[0].hourly_receipt_qty)
            let tonnage = frm.doc.total_tonnage_mt - ho_details[0].period_tonnage_running_total
            frappe.model.set_value(ho_details[0].doctype, ho_details[0].name, "day_tonnage", tonnage)
        } else {
            running_total = ho_details[index].hourly_receipt_qty + ho_details[index-1].period_tonnage_running_total
            frappe.model.set_value(ho_details[index].doctype, ho_details[index].name, "period_tonnage_running_total", running_total)
            let day_tonnage = ho_details[index-1].day_tonnage - ho_details[index].hourly_receipt_qty
            frappe.model.set_value(ho_details[index].doctype, ho_details[index].name, "day_tonnage", day_tonnage)
        }    
    }
    frm.refresh_field("hourly_operation_details")
}

let set_balance = function(frm,cdt,cdn){
    let ho_details = frm.doc.hourly_operation_details
    let length = ho_details.length
    let balance = frm.doc.total_tonnage_mt - ho_details[length-1].period_tonnage_running_total
    frm.set_value("balance",balance)
}