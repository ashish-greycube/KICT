// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Fooding", {
    setup(frm){
        frappe.db.get_single_value('Coal Settings', 'food_meal_item_group').then(group => {
            frm.set_query("meal_type", function () {
                return {
                    filters: {
                        item_group: group
                    }
                }
            })
        })
    },
	meal_type(frm) {
        frappe.call({
            method: "kict.kict.doctype.employee_fooding.employee_fooding.get_meal_price",
            args: {
                "meal_type": frm.doc.meal_type,
                "meal_date": frm.doc.meal_date
            },
            callback: function (response) {
                console.log(response.message)
                frm.set_value("meal_price",response.message)
            }
        })
	},
});
