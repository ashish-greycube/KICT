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
            frm.add_custom_button(__('Proforma Invoice for B/H'), () => create_sales_order_from_vessel_for_berth_charges(frm), __("Create"));
        }
        if (frm.is_new() == undefined) {
            const dialog_field = []
            frm.add_custom_button(__('Tax Invoice for B/H'), () => create_sales_invoice_from_vessel_for_berth_charges(frm), __("Create"));
        }   
        if (frm.is_new() == undefined) {
            frm.add_custom_button(__('Sales Invoice for C/H'), () => create_sales_invoice_for_cargo_handling_charges_from_vessel(frm), __("Create"));

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

function create_sales_invoice_from_vessel_for_berth_charges(frm) {
    if (frm.is_dirty()==true) {
        frappe.throw({
            message: __("Please save the form to proceed..."),
            indicator: "red",
        });       
    }


    frappe.call({
        method: "kict.kict.doctype.vessel.vessel.get_berth_stay_hours",
        args: {
            vessel: frm.doc.name
        },
        callback: function (r) {
            let berth_stay_hours = r.message
            if (berth_stay_hours=="0") {
                frappe.throw({
                    message: __("Berth timings are absent in statement of facts. <br> Please put timings in SOF to proceed.."),
                    indicator: "red",
                });             
            }
            else{
                let dialog = undefined
                const dialog_field = []
                   
                frappe.call({
                    method: "kict.kict.doctype.vessel.vessel.get_unique_customer_and_customer_specific_grt_from_vessel",
                    args: {
                        docname: frm.doc.name
                    },
                    callback: function (r) {
                        let customer_with_grt = r.message
                        let unique_customer = []
                        customer_with_grt.forEach(ele => {
                            unique_customer.push(ele.customer_name)
                        })
                        let bill_hours=berth_stay_hours
                        let total_qty_default=0
                        let is_bill_to = frm.doc.bh_bill_to
                        let agent_name = frm.doc.agent_name
                        let is_single_customer = false
                        let customer_specific_grt_value = frm.doc.grt
                        let customer_name
                        if (customer_with_grt.length == 1) {
                            is_single_customer = true
                            customer_name = customer_with_grt[0].customer_name
                            customer_specific_grt_value = frm.doc.grt                            
                        }
                        total_qty_default=customer_specific_grt_value*bill_hours
                        // dialog fields
                        let bill_to_field
                        let customer_specific_grt_field      
                        let total_qty_field 
                        
                        // multi customer
                        if (is_bill_to == "Customer" && is_single_customer == false) {
                            bill_to_field = {
                                fieldtype: "Select",
                                fieldname: "bill_to_field",
                                label: __("Bill To"),
                                options: unique_customer,
                                reqd: 1,
                                onchange: function () {
                                    let bill_to_name = dialog.get_field("bill_to_field")
                                    for (customer of customer_with_grt) {
                                        if (bill_to_name.value == customer.customer_name) {
                                            dialog.set_value("customer_specific_grt_field", (customer.customer_specific_grt*frm.doc.grt))
                                            dialog.set_value("customer_specific_grt_percentage",customer.customer_specific_grt)
                                        }
                                    }
                                }
                            }
                            // no default value for below
                            customer_specific_grt_field = {
                                fieldtype: "Float",
                                fieldname: "customer_specific_grt_field",
                                label: __("Customer Specific GRT"),
                                read_only: 1,
                                onchange: function () {
                                    let hrs = dialog.get_field("bill_hours")
                                    let grt = dialog.get_field("customer_specific_grt_field")
                                    let total_qty = hrs.value * grt.value
                                    dialog.set_value("total_qty", total_qty)
                                }                                
                            }
                            total_qty_field={
                                fieldtype: "Float",
                                fieldname: "total_qty",
                                label: __("Total Qty"),
                                read_only: 1,
                            }
                            
                        }     
                        // agent
                        if (is_bill_to == "Agent") {
                            bill_to_field = {
                                fieldtype: "Data",
                                fieldname: "bill_to_field",
                                label: __("Bill To"),
                                read_only: 1,
                                default: agent_name,
                                reqd: 1
                            },
                            customer_specific_grt_field = {
                                    fieldtype: "Float",
                                    fieldname: "customer_specific_grt_field",
                                    label: __("Customer Specific GRT"),
                                    read_only: 1,
                                    default: customer_specific_grt_value,
                                    onchange: function () {
                                        let hrs = dialog.get_field("bill_hours")
                                        let grt = dialog.get_field("customer_specific_grt_field")
                                        let total_qty = hrs.value * grt.value
                                        dialog.set_value("total_qty", total_qty)
                                    }                                    
                                }
                                total_qty_field={
                                    fieldtype: "Float",
                                    fieldname: "total_qty",
                                    label: __("Total Qty"),
                                    read_only: 1,
                                    default:total_qty_default
                                }                                

                        }    
                        // single customer
                        if (is_bill_to == "Customer" && is_single_customer == true) {
                            bill_to_field = {
                                fieldtype: "Data",
                                fieldname: "bill_to_field",
                                label: __("Bill To"),
                                read_only: 1,
                                default: customer_name,
                                reqd: 1
                            },
                            customer_specific_grt_field = {
                                    fieldtype: "Float",
                                    fieldname: "customer_specific_grt_field",
                                    label: __("Customer Specific GRT"),
                                    read_only: 1,
                                    default: customer_specific_grt_value,
                                    onchange: function () {
                                        let hrs = dialog.get_field("bill_hours")
                                        let grt = dialog.get_field("customer_specific_grt_field")
                                        let total_qty = hrs.value * grt.value
                                        dialog.set_value("total_qty", total_qty)
                                    }                                    
                            },
                            total_qty_field={
                                fieldtype: "Float",
                                fieldname: "total_qty",
                                label: __("Total Qty"),
                                read_only: 1,
                                default:total_qty_default
                            }                             
                        }   
                        // create and push dialog fields  
                        dialog_field.push(bill_to_field)
                        dialog_field.push({
                            fieldtype: "Section Break",
                            fieldname: "section_break_1",
                        })
                        dialog_field.push({
                            fieldtype: "Float",
                            fieldname: "bill_hours",
                            label: __("Actual Hours"),
                            default:bill_hours,
                            read_only:1
                        })
                        dialog_field.push({
                            fieldtype: "Percent",
                            fieldname: "customer_specific_grt_percentage",
                            hidden:1,
                            default:0
                        })            
                        dialog_field.push({
                            fieldtype: "Column Break",
                            fieldname: "column_break_1",
                        })
                        dialog_field.push(customer_specific_grt_field)
                        dialog_field.push({
                            fieldtype: "Column Break",
                            fieldname: "column_break_2",
                        })
                        dialog_field.push(total_qty_field)    
                        
                        dialog = new frappe.ui.Dialog({
                            title: __("Enter Details for Berth Hire Charges"),
                            fields: dialog_field,
                            primary_action_label: 'Create Tax Invoice',
                            primary_action: function (values) {
                                if (values.total_qty==undefined || values.total_qty==0) {
                                    frappe.utils.play_sound("error");
                                    frappe.throw({
                                        message: __("Total Qty cannot be zero."),
                                        indicator: "red",
                                    });
                                     
                                }                    
                                frappe.call({
                                    method: "kict.kict.doctype.vessel.vessel.create_sales_invoice_from_vessel_for_berth_charges",
                                    args: {
                                        "source_name": frm.doc.name,
                                        "target_doc": undefined,
                                        "qty": values.total_qty,
                                        "customer": values.bill_to_field,
                                        "is_single_customer":is_single_customer,
                                        "customer_specific_grt_percentage":values.customer_specific_grt_percentage,
                                        "customer_specific_grt_field":values.customer_specific_grt_field,
                                        "bill_hours":values.bill_hours,                                        
                                        "doctype": frm.doc.doctype
                                    },
                                    callback: function (response) {
                                        if (response.message) {
                                            let url_list = '<a href="/app/sales-invoice/' + response.message + '" target="_blank">' + response.message + '</a><br>'
                                            frappe.show_alert({
                                                title: __('Sales Invoice is created'),
                                                message: __(url_list),
                                                indicator: 'green'
                                            }, 12);
                                            window.open(`/app/sales-invoice/` + response.message);
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
        }
    })    
    
}

function create_sales_order_from_vessel_for_berth_charges(frm) {
    if (frm.is_dirty()==true) {
        frappe.throw({
            message: __("Please save the form to proceed..."),
            indicator: "red",
        });       
    }
    let dialog = undefined
    const dialog_field = []

    frappe.call({
        method: "kict.kict.doctype.vessel.vessel.get_unique_customer_and_customer_specific_grt_from_vessel",
        args: {
            docname: frm.doc.name
        },
        callback: function (r) {
            let customer_with_grt = r.message
            let unique_customer = []
            customer_with_grt.forEach(ele => {
                unique_customer.push(ele.customer_name)
            })

            let is_bill_to = frm.doc.bh_bill_to
            let agent_name = frm.doc.agent_name
            let is_single_customer = false
            let customer_specific_grt_value = frm.doc.grt
            let customer_name

            if (customer_with_grt.length == 1) {
                is_single_customer = true
                customer_name = customer_with_grt[0].customer_name
                customer_specific_grt_value = frm.doc.grt
            }
            // dialog fields
            let bill_to_field
            let customer_specific_grt_field

            // multi customer
            if (is_bill_to == "Customer" && is_single_customer == false) {
                bill_to_field = {
                    fieldtype: "Select",
                    fieldname: "bill_to_field",
                    label: __("Bill To"),
                    options: unique_customer,
                    reqd: 1,
                    onchange: function () {
                        let bill_to_name = dialog.get_field("bill_to_field")
                        for (customer of customer_with_grt) {
                            if (bill_to_name.value == customer.customer_name) {
                                dialog.set_value("customer_specific_grt_field", (customer.customer_specific_grt*frm.doc.grt))
                                dialog.set_value("customer_specific_grt_percentage",customer.customer_specific_grt)
                                
                                dialog.set_value("bill_hours",)
                            }
                        }
                    }
                }
                customer_specific_grt_field = {
                    fieldtype: "Float",
                    fieldname: "customer_specific_grt_field",
                    label: __("Customer Specific GRT"),
                    read_only: 1,
                }
                
            }
            // agent
            if (is_bill_to == "Agent") {
                bill_to_field = {
                    fieldtype: "Data",
                    fieldname: "bill_to_field",
                    label: __("Bill To"),
                    read_only: 1,
                    default: agent_name,
                    reqd: 1
                },
                customer_specific_grt_field = {
                        fieldtype: "Float",
                        fieldname: "customer_specific_grt_field",
                        label: __("Customer Specific GRT"),
                        read_only: 1,
                        default: customer_specific_grt_value
                    }

            }
            // single customer
            if (is_bill_to == "Customer" && is_single_customer == true) {
                bill_to_field = {
                    fieldtype: "Data",
                    fieldname: "bill_to_field",
                    label: __("Bill To"),
                    read_only: 1,
                    default: customer_name,
                    reqd: 1
                },
                customer_specific_grt_field = {
                        fieldtype: "Float",
                        fieldname: "customer_specific_grt_field",
                        label: __("Customer Specific GRT"),
                        read_only: 1,
                        default: customer_specific_grt_value
                }
            }
            // create and push dialog fields
            dialog_field.push(bill_to_field)
            dialog_field.push({
                fieldtype: "Section Break",
                fieldname: "section_break_1",
            })
            dialog_field.push({
                fieldtype: "Float",
                fieldname: "bill_hours",
                label: __("Expected Hours"),
                onchange: function () {
                    let hrs = dialog.get_field("bill_hours")
                    let grt = dialog.get_field("customer_specific_grt_field")
                    let total_qty = hrs.value * grt.value
                    dialog.set_value("total_qty", total_qty)
                }
            })
            dialog_field.push({
                fieldtype: "Percent",
                fieldname: "customer_specific_grt_percentage",
                hidden:1,
                default:0
            })            
            dialog_field.push({
                fieldtype: "Column Break",
                fieldname: "column_break_1",
            })
            dialog_field.push(customer_specific_grt_field)
            dialog_field.push({
                fieldtype: "Column Break",
                fieldname: "column_break_2",
            })
            dialog_field.push({
                fieldtype: "Float",
                fieldname: "total_qty",
                label: __("Total Qty"),
                read_only: 1,
            })

            dialog = new frappe.ui.Dialog({
                title: __("Enter Details for Berth Hire Charges"),
                fields: dialog_field,
                primary_action_label: 'Create Proforma Invoice',
                primary_action: function (values) {
                    if (values.total_qty==undefined || values.total_qty==0) {
                        frappe.utils.play_sound("error");
                        frappe.throw({
                            message: __("Total Qty cannot be zero."),
                            indicator: "red",
                        });
                         
                    }                    
                    frappe.call({
                        method: "kict.kict.doctype.vessel.vessel.create_sales_order_from_vessel_for_berth_charges",
                        args: {
                            "source_name": frm.doc.name,
                            "target_doc": undefined,
                            "qty": values.total_qty,
                            "customer": values.bill_to_field,
                            "is_single_customer":is_single_customer,
                            "customer_specific_grt_percentage":values.customer_specific_grt_percentage,
                            "customer_specific_grt_field":values.customer_specific_grt_field,
                            "bill_hours":values.bill_hours,
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

function create_sales_invoice_for_cargo_handling_charges_from_vessel(frm){
    if (frm.is_dirty()==true) {
        frappe.throw({
            message: __("Please save the form to proceed..."),
            indicator: "red",
        });       
    }
    let dialog = undefined
    const dialog_field = []

    frappe.call({
        method: "kict.kict.doctype.vessel.vessel.get_unique_item_and_customer_from_vessel",
        args: {
            docname: cur_frm.doc.name
        },
        callback: function (r) {
            let vessel_details = r.message
            let unique_cargo_item = []
            vessel_details.forEach(ele => {
                unique_cargo_item.push(ele.item)
            })
            // dialog fields
            let cargo_item_field
            let vessel_details_hex_code_field
            let customer_name_field
            let total_tonnage_field

            vessel_details_hex_code_field={
                fieldtype: "Data",
                fieldname: "vessel_details_hex_code_field",
                label: __("Vessel Detail Name"),
                // hidden:1,
            }
            customer_name_field={
                fieldtype: "Data",
                fieldname: "customer_name_field",
                label: __("Customer Name"),
                // hidden:1,
            }
            total_tonnage_field={
                fieldtype: "Data",
                fieldname: "total_tonnage_field",
                label: __("Total Tonnage"),
                // hidden:1,
            }
            // multi item
            if(vessel_details.length > 1){
                cargo_item_field = {
                    fieldtype: "Select",
                    fieldname: "cargo_item_field",
                    label: __("Cargo Item"),
                    options: unique_cargo_item,
                    columns: 2,
                    reqd: 1,
                    onchange : function(){
                        let cargo_item_name = dialog.get_field("cargo_item_field")
                        for(record of vessel_details){
                            if(record.item == cargo_item_name.value){
                                dialog.set_value("vessel_details_hex_code_field",record.name)
                                dialog.set_value("customer_name_field",record.customer_name)
                                dialog.set_value("total_tonnage_field",record.tonnage_mt)
                            }
                        }
                    }
                }
            }
            //  single item
            if(vessel_details.length == 1){
                let cargo_item=vessel_details[0].item
                cargo_item_field = {
                    fieldtype: "Data",
                    fieldname: "cargo_item_field",
                    label: __("Cargo Item"),
                    columns: 2,
                    default: cargo_item,
                    read_only: 1,
                    reqd: 1,
                }
                // put defaults
                vessel_details_hex_code_field["default"]=vessel_details[0].name
                customer_name_field["default"]=vessel_details[0].customer_name
                total_tonnage_field["default"]=vessel_details[0].tonnage_mt
            }

            dialog_field.push(cargo_item_field)
            dialog_field.push({
                fieldtype: "Section Break",
                fieldname: "section_break_1",
            })
            dialog_field.push({
                fieldtype: "Select",
                fieldname: "type_of_invoice",
                label: __("Type Of Invoice"),
                options: ["Initial" , "Complete Discharge", "Periodic Dispatch"],
                columns: 2,
                reqd: 1,
            })
            dialog_field.push(vessel_details_hex_code_field)
            dialog_field.push(customer_name_field)
            dialog_field.push(total_tonnage_field)

            dialog = new frappe.ui.Dialog({
                title: __("Enter Details for Cargo Handling Charges"),
                fields: dialog_field,
                primary_action_label: 'Create Sales Invoice',
                primary_action: function (values) {
                    frappe.call({
                        method: "kict.kict.doctype.vessel.vessel.create_sales_invoice_for_cargo_handling_charges_from_vessel",
                        args: {
                            "source_name": frm.doc.name,
                            "target_doc": undefined,
                            "cargo_item_field":values.cargo_item_field,
                            "type_of_invoice":values.type_of_invoice,
                            "vessel_details_hex_code_field":values.vessel_details_hex_code_field,
                            "customer_name_field": values.customer_name_field,
                            "total_tonnage_field":values.total_tonnage_field,
                            "doctype": frm.doc.doctype
                        },
                        callback: function (response) {
                            if (response.message) {
                                let url_list = '<a href="/app/sales-invoice/' + response.message + '" target="_blank">' + response.message + '</a><br>'
                                frappe.show_alert({
                                    title: __('Sales Order is created'),
                                    message: __(url_list),
                                    indicator: 'green'
                                }, 12);
                                window.open(`/app/sales-invoice/` + response.message);
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