// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vessel", {
    onload(frm) {
        frm.set_query("item", "vessel_details", function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {
                filters: {
                    is_stock_item: 1,
                    is_customer_provided_item: 1,
                    customer: d.customer_name
                },
            };
        });


        frappe.db.get_single_value('Coal Settings', 'customer_group_for_agent').then(group => {
            frm.set_query("agent_name", function () {
                return {
                    filters: {
                        customer_group: group
                    }
                }
            })
        })

        frm.trigger('vessel_on_refresh_load')
    },
    refresh(frm) {
        frm.trigger('vessel_on_refresh_load')
    },

    vessel_on_refresh_load: function (frm) {
        if (frm.is_new() == undefined) {
            const dialog_field = []
            frm.add_custom_button(__('Proforma Invoice for B/H'), () => create_sales_order_from_vessel(frm), __("Create"));
        }
    }
});

frappe.ui.form.on("Vessel Details", {
    item(frm, cdt, cdn) {
        let details = frm.doc.vessel_details
        let item_name = []
        for (ele of details) {
            if (ele.item) {
                if (!item_name.includes(ele.item)) {
                    item_name.push(ele.item)
                } else {
                    frappe.msgprint(__("Row {0}: You cannot select {1} again", [ele.idx, ele.item]))
                    frappe.model.set_value(cdt, cdn, "item",)
                    // frappe.model.set_value(cdt, cdn, "item_group",)
                    frappe.model.set_value(cdt, cdn, "item_name",)
                }
            }
        }
    },
    tonnage_mt(frm, cdt, cdn) {
        total_tonnage_of_vessel(frm, cdt, cdn)
    },
    vessel_details_remove: function (frm, cdt, cdn) {
        total_tonnage_of_vessel(frm, cdt, cdn)
    }
})

let total_tonnage_of_vessel = function (frm, cdt, cdn) {
    let total_tonnage = 0
    frm.doc.vessel_details.forEach(function (item) {
        total_tonnage = total_tonnage + item.tonnage_mt
    })
    frm.set_value("total_tonnage_mt", total_tonnage)
}

function create_sales_order_from_vessel(frm) {
    let dialog = undefined
    const dialog_field = []
    frappe.call({
        method: "kict.kict.doctype.vessel.vessel.get_all_unique_customer_from_vessel",
        args: {
            docname: cur_frm.doc.name
        },
        callback: function (r) {
            console.log(r.message)
            let customer_with_grt = r.message
            let unique_customer = []
            customer_with_grt.forEach(ele => {
                unique_customer.push(ele.customer_name)
            })

            let is_bill_to = frm.doc.bh_bill_to
            let agent_name = frm.doc.agent_name
            let is_single_customer = false
            let customer_specific_grt_value=frm.doc.grt
            let customer_name
            if (customer_with_grt.length == 1) {
                is_single_customer = true
                customer_name = customer_with_grt[0].customer_name
                customer_specific_grt_value=customer_with_grt[0].customer_specific_grt
            }
            let bill_to
            let customer_specific_grt
            if (is_bill_to == "Customer" && is_single_customer == false) {
                bill_to = {
                    fieldtype: "Select",
                    fieldname: "bill_to",
                    label: __("Bill To"),
                    options: unique_customer,
                    in_list_view: 1,
                    columns: 2,
                    reqd: 1,
                    onchange: function () {
                        let bill_to_name = dialog.get_field("bill_to")
                        console.log(bill_to_name.value)
                        for (customer of customer_with_grt) {
                            if (bill_to_name.value == customer.customer_name) {
                                dialog.set_value("customer_specific_grt", customer.customer_specific_grt)
                            }
                        }

                    }
                }
                customer_specific_grt={
                    fieldtype: "Float",
                    fieldname: "customer_specific_grt",
                    label: __("Customer Specific GRT"),
                    in_list_view: 1,
                    read_only: 1,
                }
            }

            if (is_bill_to == "Agent" ) {
                bill_to = {
                    fieldtype: "Data",
                    fieldname: "bill_to",
                    label: __("Bill To"),
                    read_only: 1,
                    in_list_view: 1,
                    columns: 2,
                    default: agent_name,
                    reqd: 1
                },
                customer_specific_grt={
                    fieldtype: "Float",
                    fieldname: "customer_specific_grt",
                    label: __("Customer Specific GRT"),
                    in_list_view: 1,
                    read_only: 1,
                    default:customer_specific_grt_value
                }                

            }
            if (is_bill_to == "Customer" && is_single_customer == true) {
                bill_to = {
                    fieldtype: "Data",
                    fieldname: "bill_to",
                    label: __("Bill To"),
                    read_only: 1,
                    in_list_view: 1,
                    columns: 2,
                    default: customer_name,
                    reqd: 1
                },
                customer_specific_grt={
                    fieldtype: "Float",
                    fieldname: "customer_specific_grt",
                    label: __("Customer Specific GRT"),
                    in_list_view: 1,
                    read_only: 1,
                    default:customer_specific_grt_value
                }                 

            }
            dialog_field.push(bill_to)

      
            dialog_field.push({
                fieldtype: "Section Break",
                fieldname: "section_break_1",
            })
            dialog_field.push({
                fieldtype: "Float",
                fieldname: "bill_hours",
                label: __("Expected Hours"),
                in_list_view: 1,
                onchange: function () {
                    let hrs = dialog.get_field("bill_hours")
                    let grt = dialog.get_field("customer_specific_grt")
                    if (grt.value) {
                        let total_qty = hrs.value * grt.value
                        dialog.set_value("total_qty", total_qty)
                    }
                    else {
                        if (frm.doc.bh_bill_to == "Agent") {
                            let total_qty = hrs.value * frm.doc.grt
                            dialog.set_value("total_qty", total_qty)
                        }
                        else {
                            grt = customer_with_grt[0].customer_specific_grt
                            let total_qty = hrs.value * grt
                            dialog.set_value("total_qty", total_qty)
                        }
                    }
                }
            })
            dialog_field.push({
                fieldtype: "Column Break",
                fieldname: "column_break_1",
            })
            dialog_field.push(customer_specific_grt)
            dialog_field.push({
                fieldtype: "Column Break",
                fieldname: "column_break_2",
            })
            dialog_field.push({
                fieldtype: "Float",
                fieldname: "total_qty",
                label: __("Total Qty"),
                in_list_view: 1,
                read_only: 1,
            })

            // if (customer_with_grt.length == 1){
            //     let bill_to_name = dialog.get_field("bill_to")
            //     console.log(bill_to_name)
            //     for (customer of customer_with_grt) {
            //         if (bill_to_name.value == customer.customer_name) {
            //             dialog.set_value("customer_specific_grt", customer.customer_specific_grt)
            //         }
            //     }
            // }
            //     let bill_to_name = dialog.get_field("bill_to")
            // for (customer of customer_with_grt) {
            //     if (bill_to_name.value == customer.customer_name) {
            //         dialog.set_value("customer_specific_grt", customer.customer_specific_grt)
            //     }
            // }

            dialog = new frappe.ui.Dialog({
                title: __("Enter Details for Berth Hire Charges"),
                fields: dialog_field,
                primary_action_label: 'Create Proforma Invoice',
                primary_action: function (values) {
                    frappe.call({
                        method: "kict.kict.doctype.vessel.vessel.create_sales_order_from_vessel",
                        args: {
                            "source_name": frm.doc.name,
                            "target_doc": undefined,
                            "hrs": values.bill_hours,
                            "qty": values.total_qty,
                            "customer": values.bill_to,
                            "doctype": frm.doc.doctype
                        },
                        callback: function (response) {
                            if (response.message) {
                                let url_list = '<a href="/app/sales-order/' + response.message + '" target="_blank">' + response.message + '</a><br>'
                                frappe.show_alert({
                                    title: __('Sales Order is created'),
                                    message: __(url_list),
                                    indicator: 'green'
                                }, 12);
                                window.open(`/app/sales-order/` + response.message);
                            }
                        }
                    });
                    dialog.hide();
                }
            })
            dialog.show()
        }
    })
}