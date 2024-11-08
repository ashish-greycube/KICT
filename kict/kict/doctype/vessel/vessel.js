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

        frappe.db.get_single_value('Coal Settings', 'customer_group_for_agent').then(group => {
            frm.set_query("opa", function () {
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
            frm.add_custom_button(__('Proforma Invoice for B/H'), () => create_sales_order_from_vessel_for_berth_charges(frm), __("Create"));
        }
        if (frm.is_new() == undefined) {
            frm.add_custom_button(__('Tax Invoice for B/H'), () => create_sales_invoice_from_vessel_for_berth_charges(frm), __("Create"));
        }   
        if (frm.is_new() == undefined) {
            frm.add_custom_button(__('Tax invoice for C/H'), () => create_sales_invoice_for_cargo_handling_charges_from_vessel(frm), __("Create"));
        }
        if (frm.is_new() == undefined) {
            frm.add_custom_button(__('Tax Invoice for S/C'), () => create_sales_invoice_for_storage_charges_from_vessel(frm), __("Create"));
        }
        if (frm.is_new() == undefined) {
            frm.add_custom_button(__('Storage Charges Report'), () => show_storage_charges_report_from_vessel(frm));
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
                        let opa_name = frm.doc.opa
                        let is_single_customer = false
                        let vessel_level_grt_value = flt(frm.doc.grt)
                        let customer_name
                        if (customer_with_grt.length == 1) {
                            is_single_customer = true
                            customer_name = customer_with_grt[0].customer_name                                                   
                        }
                        total_qty_default=vessel_level_grt_value*bill_hours
                        // dialog fields
                        let bill_to_field
                        let customer_specific_grt_field      
                        let total_qty_field 
                        let customer_po_no_field
                        let vessel_level_grt_field
                        let customer_specific_grt_percentage
                        
                        customer_po_no_field={
                            fieldtype: "Data",
                            fieldname: "customer_po_no_field",
                            label: __("Customer PO No"),
                            read_only: 1,
                            // hidden:1,
                        }
                        total_qty_field={
                            fieldtype: "Float",
                            fieldname: "total_qty",
                            label: __("Total Qty"),
                            read_only: 1,
                            precision:9
                        }
                        proportionate_berth_hours_field={
                            fieldtype: "Float",
                            fieldname: "proportionate_berth_hours_field",
                            label: __("Proportionate Berth Hours"),
                            read_only: 1, 
                            precision:9                           
                        }
                        vessel_level_grt_field = {
                            fieldtype: "Float",
                            fieldname: "vessel_level_grt_field",
                            label: __("Vessel GRT"),
                            read_only: 1,
                            default:frm.doc.grt
                        }
                        customer_specific_grt_percentage = {
                            fieldtype: "Percent",
                            fieldname: "customer_specific_grt_percentage",
                            label: __("Customer Specific GRT %"),
                            hidden:0 ,
                            read_only: 1,
                        }
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
                                            dialog.set_value("proportionate_berth_hours_field",flt((customer.customer_specific_grt/100)*bill_hours))
                                            dialog.set_value("customer_specific_grt_field", ((customer.customer_specific_grt*vessel_level_grt_value))/100)
                                            dialog.set_value("customer_specific_grt_percentage",customer.customer_specific_grt)
                                            dialog.set_value("customer_po_no_field",customer.customer_po_no)
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
                                hidden:0,
                                onchange: function () {
                                    let proportionate_berth_hours = dialog.get_field("proportionate_berth_hours_field")
                                    let total_qty = proportionate_berth_hours.value * vessel_level_grt_value
                                    dialog.set_value("total_qty", total_qty)
                                }                                
                            }
                          
                        }     
                        // agent
                        if (is_bill_to == "Agent" || is_bill_to =="OPA") {
                            bill_to_field = {
                                fieldtype: "Data",
                                fieldname: "bill_to_field",
                                label: __("Bill To"),
                                read_only: 1,
                                reqd: 1
                            }
                            if (is_bill_to == "OPA"){
                                bill_to_field["default"]=opa_name
                            }else if(is_bill_to == "Agent"){
                                bill_to_field["default"]=agent_name
                            }
                            proportionate_berth_hours = (vessel_level_grt_value/vessel_level_grt_value)*bill_hours
                            proportionate_berth_hours_field["default"]=flt(proportionate_berth_hours)
                            customer_specific_grt_field = {
                                    fieldtype: "Float",
                                    fieldname: "customer_specific_grt_field",
                                    label: __("Customer Specific GRT"),
                                    read_only: 1,
                                    default: vessel_level_grt_value,
                                    hidden:1,
                                    onchange: function () {
                                        let proportionate_berth_hours_value = dialog.get_field("proportionate_berth_hours_field")
                                        let total_qty = proportionate_berth_hours_value.value * vessel_level_grt_value 
                                        dialog.set_value("total_qty", total_qty)
                                    }                                    
                                }
                            total_qty_field["default"]=proportionate_berth_hours*vessel_level_grt_value
                            customer_specific_grt_percentage["default"]=flt(100)
                            customer_specific_grt_percentage["label"]="GRT %"                                

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
                            proportionate_berth_hours = (vessel_level_grt_value/frm.doc.grt)*bill_hours
                            proportionate_berth_hours_field["default"]=flt(proportionate_berth_hours)
                            customer_specific_grt_field = {
                                    fieldtype: "Float",
                                    fieldname: "customer_specific_grt_field",
                                    label: __("Customer Specific GRT"),
                                    read_only: 1,
                                    default: vessel_level_grt_value,
                                    hidden:1,
                                    onchange: function () {
                                        let proportionate_berth_hours_value = dialog.get_field("proportionate_berth_hours_field")
                                        let total_qty = proportionate_berth_hours_value.value * vessel_level_grt_value 
                                        dialog.set_value("total_qty", total_qty)
                                    }                                    
                            },
                            total_qty_field["default"]=proportionate_berth_hours * vessel_level_grt_value
                            customer_po_no_field["default"]=customer_with_grt[0].customer_po_no
                            customer_specific_grt_percentage["default"]= flt(customer_with_grt[0].customer_specific_grt)     
                            customer_specific_grt_percentage["label"]="GRT %"                             
                        }   
                        // create and push dialog fields  
                        dialog_field.push(bill_to_field)
                        dialog_field.push({fieldtype: "Section Break",fieldname: "section_break_1"})
                        dialog_field.push({
                            fieldtype: "Float",
                            fieldname: "bill_hours",
                            label: __("Actual Hours"),
                            default:bill_hours,
                            read_only:1
                        })
                        dialog_field.push({fieldtype: "Column Break",fieldname: "column_break_1"})
                        dialog_field.push(vessel_level_grt_field)
                        dialog_field.push({fieldtype: "Column Break",fieldname: "column_break_2"})
                        dialog_field.push(customer_specific_grt_percentage)        
                        dialog_field.push({fieldtype: "Column Break",fieldname: "column_break_3"})
                        dialog_field.push(customer_specific_grt_field)
                        dialog_field.push({fieldtype: "Section Break",fieldname: "section_break_2"})
                        dialog_field.push(proportionate_berth_hours_field)
                        dialog_field.push({fieldtype: "Column Break",fieldname: "column_break_4"})
                        dialog_field.push(total_qty_field)
                        dialog_field.push({fieldtype: "Column Break",fieldname: "column_break_5"})
                        dialog_field.push(customer_po_no_field)    
                        
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
                                        "customer_po_no_field":values.customer_po_no_field,
                                        "bill_hours":values.bill_hours,
                                        "proportionate_berth_hours_field":values.proportionate_berth_hours_field,                                        
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
            let opa_name = frm.doc.opa
            let is_single_customer = false
            let customer_specific_grt_value
            let vessel_level_grt_value= frm.doc.grt 
            let customer_name

            if (customer_with_grt.length == 1) {
                is_single_customer = true
                customer_name = customer_with_grt[0].customer_name
                customer_specific_grt_value = vessel_level_grt_value
               
            }
            // dialog fields
            let bill_to_field
            let customer_specific_grt_field
            let customer_po_no_field
            let customer_specific_grt_percentage
            let vessel_level_grt_field

            customer_po_no_field={
                fieldtype: "Data",
                fieldname: "customer_po_no_field",
                label: __("Customer PO No"),
                read_only: 1,
                // hidden:1,
            }
            customer_specific_grt_field = {
                fieldtype: "Float",
                fieldname: "customer_specific_grt_field",
                label: __("Customer Specific GRT"),
                read_only: 1,
                hidden:1
            }            
            vessel_level_grt_field = {
                fieldtype: "Float",
                fieldname: "vessel_level_grt_field",
                label: __("Vessel GRT"),
                read_only: 1,
                default:frm.doc.grt
            }
            customer_specific_grt_percentage={                
                fieldtype: "Percent",
                fieldname: "customer_specific_grt_percentage",
                label: __("Customer Specific GRT %"),
                hidden:0 ,
                read_only: 1,              
            }
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
                                dialog.set_value("customer_specific_grt_field", ((customer.customer_specific_grt*frm.doc.grt))/100)
                                dialog.set_value("customer_specific_grt_percentage",flt(customer.customer_specific_grt))
                                dialog.set_value("customer_po_no_field",customer.customer_po_no)
                                dialog.set_value("bill_hours",0)
                            }
                        }
                    }
                }
                customer_specific_grt_field["hidden"]=0
            }
            // agent
            if (is_bill_to == "Agent" || is_bill_to =="OPA") {
                bill_to_field = {
                    fieldtype: "Data",
                    fieldname: "bill_to_field",
                    label: __("Bill To"),
                    read_only: 1,
                    reqd: 1
                }
                if (is_bill_to == "OPA"){
                    bill_to_field["default"]=opa_name
                }else if(is_bill_to == "Agent"){
                    bill_to_field["default"]=agent_name
                }
                customer_specific_grt_field["default"]=vessel_level_grt_value               
                customer_specific_grt_percentage["default"]=flt(100)
                customer_specific_grt_percentage["label"]="GRT %"

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
                customer_specific_grt_field["default"]=vessel_level_grt_value
                customer_po_no_field["default"]=customer_with_grt[0].customer_po_no
                customer_specific_grt_percentage["default"]= flt(customer_with_grt[0].customer_specific_grt)     
                customer_specific_grt_percentage["label"]="GRT %"         
            }
            // create and push dialog fields
            dialog_field.push(bill_to_field)
            dialog_field.push({fieldtype: "Section Break",fieldname: "section_break_1"})
            dialog_field.push({
                fieldtype: "Float",
                fieldname: "bill_hours",
                label: __("Expected Hours"),
                onchange: function () {
                    let hrs = dialog.get_field("bill_hours")
                    let grt = dialog.get_field("customer_specific_grt_percentage")
                    console.log((flt(grt.value)/100)*flt(hrs),'9',hrs.value,grt.value)
                    dialog.set_value("proportionate_berth_hours_field",(flt(grt.value)/100)*flt(hrs.value))
                    // let total_qty = hrs.value * grt.value
                    // dialog.set_value("total_qty", total_qty)
                }
            })
            
            dialog_field.push({fieldtype: "Column Break",fieldname: "column_break_1"})
            dialog_field.push(vessel_level_grt_field)
            dialog_field.push({fieldtype: "Column Break",fieldname: "column_break_2"})
            dialog_field.push(customer_specific_grt_percentage)
            dialog_field.push({fieldtype: "Column Break",fieldname: "column_break_3"})
            dialog_field.push(customer_specific_grt_field)
            dialog_field.push({fieldtype: "Section Break",fieldname: "section_break_2"})
            dialog_field.push({
                fieldtype: "Float",
                fieldname: "proportionate_berth_hours_field",
                label: __("Proportionate Berth Hours"),
                precision:9,
                read_only: 1,
                onchange: function (frm){
                    let proportionate_berth_hours = dialog.get_field("proportionate_berth_hours_field")
                    let vessel_level_grt_field_value=dialog.get_field("vessel_level_grt_field")                     
                    dialog.set_value("total_qty",flt(proportionate_berth_hours.value) * flt(vessel_level_grt_field_value.value))
                }                            
            })
            dialog_field.push({fieldtype: "Column Break",fieldname: "column_break_4"})
            dialog_field.push({
                fieldtype: "Float",
                fieldname: "total_qty",
                label: __("Total Qty"),
                read_only: 1,
                precision:9
            })
            dialog_field.push({fieldtype: "Column Break",fieldname: "column_break_5"})
            dialog_field.push(customer_po_no_field) 

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
                            "customer_po_no_field":values.customer_po_no_field,
                            "bill_hours":values.bill_hours,
                            "proportionate_berth_hours_field":values.proportionate_berth_hours_field,
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
        method: "kict.kict.doctype.vessel.vessel.get_unique_item",
        args: {
            docname: cur_frm.doc.name
        },
        callback: function (r) {
            let vessel_items = r.message
            let unique_cargo_item = []
            vessel_items.forEach(ele => {
                unique_cargo_item.push(ele.item)
            })
            let billing_option_list
            let participating_rr_details

            // dialog fields
            let cargo_item_field
            let customer_name_field
            let type_of_billing_field
            let is_periodic_or_dispatch_field
            let rate_field
            let from_date_field
            let to_date_field
            let periodic_cargo_qty
            let non_periodic_cargo_qty
            let get_qty_button_field
            let customer_po_no_field
            let participant_detail_field

            cargo_item_field = {
                fieldtype: "Select",
                fieldname: "cargo_item_field",
                label: __("Cargo Item"),
                options: unique_cargo_item,
                columns: 2,
                reqd: 1,
                onchange : function(){
                    let cargo_item_name = dialog.get_field("cargo_item_field")
                    frappe.call({
                        method: "kict.kict.doctype.vessel.vessel.get_customer_and_tonnage_based_on_cargo_item",
                        args: {
                            item_code: cargo_item_name.value,
                            docname: cur_frm.doc.name
                        },
                        callback: function (r) {
                            let customer_name = r.message[0].customer_name
                            let cargo_item_tonnage = r.message[0].tonnage_mt
                            let customer_po_no = r.message[0].customer_po_no
                            dialog.set_value("customer_name_field",customer_name)
                            dialog.set_value("non_periodic_cargo_qty",cargo_item_tonnage)
                            dialog.set_value("customer_po_no_field",customer_po_no)
                        }
                    })
                }
            }
            
            customer_name_field={
                fieldtype: "Data",
                fieldname: "customer_name_field",
                label: __("Customer Name"),
                read_only:1,
                // hidden:1,
                onchange : function(){
                    let customer_name = dialog.get_field("customer_name_field")
                    frappe.call({
                        method: "kict.kict.doctype.vessel.vessel.get_cargo_handling_option_name_and_is_periodic_or_not_based_on_customer",
                        args: {
                            docname: cur_frm.doc.name,
                            customer_name: customer_name.value
                        },
                        callback: function (r) {
                            billing_option_list = r.message
                            let billing_option = []
                            if (billing_option_list.length > 0){
                                billing_option_list.forEach(ele=>{
                                    billing_option.push(ele.cargo_handling_option_name)
                                })
                            }
                            else {
                                let customer_url = '<a href="/app/customer/' + customer_name.value + '" target="_blank">' + customer_name.value + '</a><br>'
                                dialog.hide()
                                frappe.throw(__("Cargo charges configuration not found in customer {0}",[customer_url]))
                                
                            }
                            dialog.set_df_property('type_of_billing_field','options',billing_option)
                        }
                    })
                }
            }
            type_of_billing_field={
                fieldtype: "Select",
                fieldname: "type_of_billing_field",
                label: __("Type Of Billing"),
                options:[""],
                onchange: function(){
                    console.log('inside type of billing')
                    let billing_option = dialog.get_field("type_of_billing_field")
                    let customer_name = dialog.get_field("customer_name_field")
                    for (let row of billing_option_list){
                        if (billing_option.value == row.cargo_handling_option_name){
                            dialog.set_value("is_periodic_or_dispatch_field",row.billing_type)
                        }
                    }
                    // console.log(dialog.get_field("is_periodic_or_dispatch_field").value)
                    let is_periodic_or_dispatch_field=dialog.get_field("is_periodic_or_dispatch_field").value
                    if (is_periodic_or_dispatch_field!='Non-Periodic') {
                        console.log('before call')
                        frappe.call({
                            method: "kict.kict.doctype.vessel.vessel.get_from_date_for_dispatch_periodic_type",
                            args: {
                                'vessel': frm.doc.name,
                                'cargo_item_field': dialog.get_field("cargo_item_field").value,
                                'type_of_billing_field':dialog.get_field("type_of_billing_field").value || undefined,
                            },
                            callback: function (r) {
                                console.log(r)
                                let get_from_date_for_dispatch_periodic_type=r.message
                                dialog.set_value("from_date_field",get_from_date_for_dispatch_periodic_type.from_date)
                                dialog.set_value("to_date_field",frappe.datetime.add_days(frappe.datetime.nowdate(),-1))
                                dialog.set_df_property('cargo_item_field','read_only',1)
                                    
                            }
                        })                         
                    }
                   

                }
            }
            is_periodic_or_dispatch_field={
                fieldtype: "Select",
                fieldname: "is_periodic_or_dispatch_field",
                label: __("Is Periodic or Dispatch?"),
                options:["Non-Periodic", "Periodic", "Dispatch"],
                read_only:1,
                onchange: function(){
                    let periodic_option = dialog.get_field("is_periodic_or_dispatch_field")
                    if(periodic_option.value == "Periodic"){
                        dialog.set_df_property('from_date_field','hidden',0)
                        dialog.set_df_property('to_date_field','hidden',0)
                        dialog.set_df_property('periodic_cargo_qty','hidden',0)
                        dialog.set_df_property('non_periodic_cargo_qty','hidden',1)
                        dialog.set_df_property('get_qty_button_field','hidden',0)
                    }
                    else{
                        dialog.set_df_property('from_date_field','hidden',1)
                        dialog.set_df_property('to_date_field','hidden',1)
                        dialog.set_df_property('periodic_cargo_qty','hidden',1)
                        dialog.set_df_property('non_periodic_cargo_qty','hidden',0)
                        dialog.set_df_property('get_qty_button_field','hidden',1)
                    }
                    let cargo_item_name = dialog.get_field("cargo_item_field")
                    let billing_option = dialog.get_field("type_of_billing_field")
                    let customer_name = dialog.get_field("customer_name_field")
                    frappe.call({
                        method: "kict.kict.doctype.vessel.vessel.get_cargo_handling_rate_for_customer_based_on_billing_type",
                        args: {
                            docname: cur_frm.doc.name,
                            item_code:cargo_item_name.value,
                            customer: customer_name.value,
                            billing_type:billing_option.value
                        },
                        callback: function (r) {
                            dialog.set_value("rate_field",r.message)
                        }
                    })
                }
            }
            rate_field={
                fieldtype: "Currency",
                fieldname: "rate_field",
                label: __("Rate"),
                read_only:1
            }
            from_date_field={
                fieldtype: "Date",
                fieldname: "from_date_field",
                label: __("From Date"),
                hidden:1
            }
            to_date_field={
                fieldtype: "Date",
                fieldname: "to_date_field",
                label: __("To Date"),
                hidden:1,
                onchange: function(){
                    let user_to_date =  dialog.get_field("to_date_field")
                    if (user_to_date.value > frappe.datetime.nowdate()){
                        frappe.throw({
                            message: __("To Date could not greater than today."),
                            indicator: "red",
                        });
                    }
                }                
            }
            periodic_cargo_qty={
                fieldtype: "Float",
                fieldname: "periodic_cargo_qty",
                label: __("Periodic Qty"),
                hidden:1,
                read_only:1
            }
            non_periodic_cargo_qty={
                fieldtype: "Float",
                fieldname: "non_periodic_cargo_qty",
                label: __("Qty"),
                // hidden:1,
                read_only:1
            }
            customer_po_no_field={
                fieldtype: "Data",
                fieldname: "customer_po_no_field",
                label: __("Customer PO No"),
                read_only: 1
                // hidden:1,
            }
            get_qty_button_field={
                fieldtype: "Button",
                fieldname: "get_qty_button_field",
                label: __("Get Quantity"),
                hidden:1,
                click : () => {
                    console.log("button clicked")
                    frappe.call({
                        method: "kict.kict.doctype.vessel.vessel.get_qty_for_dispatch_periodic_type",
                        args: {
                            'vessel': frm.doc.name,
                            'cargo_item_field': dialog.get_field("cargo_item_field").value,
                            'from_date_field': dialog.get_field("from_date_field").value  || undefined,
                            'to_date_field': dialog.get_field("to_date_field").value   || undefined,
                        },
                        callback: function (r) {
                            console.log(r)
                            let get_qty_for_dispatch_periodic_type=r.message[0]
                            get_qty_for_dispatch_periodic_type.forEach(date_range_row => {
                                dialog.set_value("periodic_cargo_qty",date_range_row.rr_item_weight_mt)
                            });
                            rr_item_detail_html=r.message[1]
                            dialog.set_df_property('participant_detail_field','options',rr_item_detail_html)
                            console.log(participating_rr_details,"participating_rr_details")
                        }
                    })                     
                }
            }
            participant_detail_field={
                fieldtype: "HTML",
                fieldname: "participant_detail_field",
                read_only:1,
                options:""
            }
            dialog_field.push(cargo_item_field)
            dialog_field.push({
                fieldtype: "Section Break",
                fieldname: "section_break_1",
            })
            dialog_field.push(customer_name_field)
            dialog_field.push(type_of_billing_field)
            dialog_field.push(is_periodic_or_dispatch_field)
            dialog_field.push(rate_field)
            dialog_field.push(from_date_field)
            dialog_field.push(to_date_field)
            dialog_field.push(get_qty_button_field)
            dialog_field.push(periodic_cargo_qty)
            dialog_field.push(non_periodic_cargo_qty)
            dialog_field.push(participant_detail_field)
            dialog_field.push(customer_po_no_field)

            dialog = new frappe.ui.Dialog({
                title: __("Enter Details for Cargo Handling Charges"),
                fields: dialog_field,
                primary_action_label: 'Create Sales Invoice',
                primary_action: function (values) {
                    console.log(values,"values")
                    if ((values.is_periodic_or_dispatch_field == "Periodic") && (values.periodic_cargo_qty == undefined || 0)){
                        frappe.throw(__("Qty cannot be zero"))
                    }
                    frappe.call({
                        method: "kict.kict.doctype.vessel.vessel.create_sales_invoice_for_cargo_handling_charges_from_vessel",
                        args: {
                            "source_name": frm.doc.name,
                            "target_doc": undefined,
                            "cargo_item_field":values.cargo_item_field,
                            "customer_name_field": values.customer_name_field,
                            "type_of_billing_field":values.type_of_billing_field,
                            "is_periodic_or_dispatch_field":values.is_periodic_or_dispatch_field,
                            "rate_field":values.rate_field,
                            "periodic_cargo_qty":values.periodic_cargo_qty,
                            "non_periodic_cargo_qty":values.non_periodic_cargo_qty,
                            "customer_po_no_field":values.customer_po_no_field,
                            "from_date_field":values.from_date_field,
                            "to_date_field": values.to_date_field,
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

function create_sales_invoice_for_storage_charges_from_vessel(frm){
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
            docname: frm.doc.name
        },
        callback: function (r) {
            let vessel_details = r.message
            let unique_cargo_item = []
            vessel_details.forEach(ele => {
                unique_cargo_item.push(ele.item)
            })
            // dialog fields
            let cargo_item_field
            let customer_name_field
            let total_tonnage_field
            let customer_po_no_field

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
            customer_po_no_field={
                fieldtype: "Data",
                fieldname: "customer_po_no_field",
                label: __("Customer PO No"),
                read_only: 1
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
                                dialog.set_value("customer_name_field",record.customer_name)
                                dialog.set_value("total_tonnage_field",record.tonnage_mt)
                                dialog.set_value("customer_po_no_field",record.customer_po_no)
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
                customer_name_field["default"]=vessel_details[0].customer_name
                total_tonnage_field["default"]=vessel_details[0].tonnage_mt
                customer_po_no_field["default"]=vessel_details[0].customer_po_no
            }
            dialog_field.push(cargo_item_field)
            dialog_field.push({
                fieldtype: "Section Break",
                fieldname: "section_break_1",
            })
            dialog_field.push(customer_name_field)
            dialog_field.push(total_tonnage_field)
            dialog_field.push(customer_po_no_field)
            dialog_field.push({
                label: 'Message',
				fieldname: 'msg',
				fieldtype: 'HTML',
				options: '<p class="alert alert-warning">You can create tax invoice of storage charges <b>ONLY IF</b>, there are stock entry/s such that stock balance is zero </p>',
            })

            dialog = new frappe.ui.Dialog({
                title: __("Enter Details for Storage Charges"),
                fields: dialog_field,
                primary_action_label: 'Create Sales Invoice',
                primary_action: function (values) {
                    frappe.call({
                        method: "kict.kict.doctype.vessel.vessel.create_sales_invoice_for_storage_charges_from_vessel",
                        args: {
                            "source_name": frm.doc.name,
                            "target_doc": undefined,
                            "cargo_item_field":values.cargo_item_field,
                            "customer_name_field": values.customer_name_field,
                            "total_tonnage_field":values.total_tonnage_field,
                            "customer_po_no_field":values.customer_po_no_field,
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

function show_storage_charges_report_from_vessel(frm) {
    let dialog = undefined
    const dialog_field = []

    frappe.call({
        method: "kict.kict.doctype.vessel.vessel.get_unique_customer_form_vessel",
        args: {
            docname: frm.doc.name
        },
        callback: function (r) {
            let values = r.message
            let unique_customer = []
            values.forEach(element => {
                unique_customer.push(element.customer_name)
            });

            let customer_name_field
            let cargo_item_field
            customer_name_field={
                fieldtype: "Select",
                fieldname: "customer_name_field",
                label: __("Customer Name"),
                options: unique_customer,
                onchange: function(){
                    let customer_name = dialog.get_field("customer_name_field")
                    frappe.call({
                        method: "kict.kict.doctype.vessel.vessel.get_item_based_on_customer",
                        args: {
                            docname: cur_frm.doc.name,
                            customer: customer_name.value,
                        },
                        callback: function (r) {
                            let values = r.message
                            if (values.length == 1){
                                dialog.set_value("cargo_item_field",values[0].item) 
                            } 
                            let item_list = []
                            values.forEach(ele => {
                                item_list.push(ele.item)
                            });
                            dialog.set_df_property("cargo_item_field","options",item_list) 
                        }
                    })
                }
            }
            if (unique_customer.length==1) {
                customer_name_field["default"]=unique_customer[0]
                frappe.call({
                    method: "kict.kict.doctype.vessel.vessel.get_item_based_on_customer",
                    args: {
                        docname: cur_frm.doc.name,
                        customer: unique_customer[0]
                    },
                    callback: function (r) {
                        let values = r.message
                        if (values.length == 1){
                            dialog.set_value("cargo_item_field",values[0].item) 
                        } 
                        let item_list = []
                        values.forEach(ele => {
                            item_list.push(ele.item)
                        });
                        dialog.set_df_property("cargo_item_field","options",item_list) 
                    }
                })
            }
            cargo_item_field = {
                fieldtype: "Select",
                fieldname: "cargo_item_field",
                label: __("Cargo Item"),
            }
            dialog_field.push(customer_name_field)
            dialog_field.push(cargo_item_field)

            dialog = new frappe.ui.Dialog({
                title: __("Enter Details for Storage Charges"),
                fields: dialog_field,
                primary_action_label: 'Show Report',
                primary_action: function (values) {
                    console.log(values)
                    frappe.open_in_new_tab = true;
					frappe.route_options = {
                        vessel: frm.doc.name,
                        customer: values.customer_name_field,
                        customer_item: values.cargo_item_field
					};                    
                    frappe.set_route("query-report", "Storage Charges");
                    dialog.hide();                    
                }
            })
            dialog.show()
        }
    })
}