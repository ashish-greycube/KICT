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
    const dialog_field = []
    frappe.call({
        method: "kict.kict.doctype.vessel.vessel.get_all_unique_customer_from_vessel",
        args: {
            docname: cur_frm.doc.name
        },
        callback: function (r) {
            let customer = r.message
            let unique_customer = [""]
            customer.forEach(ele => {
                unique_customer.push(ele.customer_name)
            })
            if (dialog_field.length == 0) {
                if (cur_frm.doc.bh_bill_to == "Agent") {
                    let bill_to = {
                        fieldtype: "Data",
                        fieldname: "bill_to",
                        label: __("Bill To"),
                        read_only: 1,
                        in_list_view: 1,
                        columns: 2,
                        default: cur_frm.doc.agent_name,
                        reqd: 1
                    }
                    dialog_field.push(bill_to)
                }
                else {
                    if (customer.length == 1) {
                        let bill_to = {
                            fieldtype: "Data",
                            fieldname: "bill_to",
                            label: __("Bill To"),
                            read_only: 1,
                            in_list_view: 1,
                            columns: 2,
                            default: customer[0].customer_name,
                            reqd: 1
                        }
                        dialog_field.push(bill_to)
                    } else {
                        let bill_to = {
                            fieldtype: "Select",
                            fieldname: "bill_to",
                            label: __("Bill To"),
                            options: unique_customer,
                            in_list_view: 1,
                            columns: 2,
                            reqd: 1
                        }
                        dialog_field.push(bill_to)
                    }
                }
            }
            if (dialog_field.length < 2) {
                dialog_field.push({
                    fieldtype: "Float",
                    fieldname: "bill_hours",
                    label: __("Expected Hours"),
                    in_list_view: 1,
                })
            }

            const dialog = new frappe.ui.Dialog({
                title: __("Enter Details for Berth Hire Charges"),
                fields: dialog_field,
                primary_action_label: 'Create Proforma Invoice',
                primary_action: function (values) {
                    frappe.call({
                        method: "kict.kict.doctype.vessel.vessel.create_sales_order_from_vessel",
                        args: {
                            "source_name": cur_frm.doc.name,
                            "target_doc": undefined,
                            "hrs": values.bill_hours,
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