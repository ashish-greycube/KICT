frappe.ui.form.on("Agents DO", {
    onload(frm) {
        frm.trigger("item_and_customer_filter")
    },
    vessel(frm) {
        frm.trigger("item_and_customer_filter")
    },
    item_and_customer_filter: function (frm) {
        frappe.db.get_list("Vessel Details", {
            parent_doctype: "Vessel",
            filters: {
                "parent": frm.doc.vessel
            },
            fields: ["commodity", "grade", "customer_name"]
        }).then(records => {
                let cargo_commodity = []
                let grade = []
                let customer_list = []
    
                records.forEach(r => {
                    cargo_commodity.push(r.commodity)
                    grade.push(r.grade)
                    customer_list.push(r.customer_name)
                })
                let unique_commodity = [...new Set(cargo_commodity)];
                let unique_grade = [...new Set(grade)];
                let unique_customer_list = [...new Set(customer_list)];
    
                frm.set_query("cargo__name", "agents_do_detail", function () {
                    let return_filters = {}
                    if(frm.doc.vessel){
                        return_filters["name"]= ["in", unique_commodity]
                    }
                    else{
                        return_filters["name"]=["in", '']
                    }
                    return {
                        filters:return_filters
                    }

                });
                frm.set_query("cargo_grade", "agents_do_detail", function () {
                    let return_filters = {}
                    if(frm.doc.vessel){
                        return_filters["name"]= ["in", unique_grade]
                    }
                    else{
                        return_filters["name"]=["in", '']
                    }
                    return {
                        filters:return_filters
                    }
                });
                frm.set_query("importer_name", function () {
                    let return_filters = {}
                    if(frm.doc.vessel){
                        return_filters["name"]= ["in", unique_customer_list]
                    }
                    else{
                        return_filters["name"]=["in", '']
                    }
                    return {
                        filters:return_filters
                    }
                });
        })
    }
});

frappe.ui.form.on("Agents DO Detail", {
    do_received_qty(frm, cdt, cdn) {
        set_do_balance_qty(frm, cdt, cdn)
    },
    agents_do_detail_remove(frm, cdt, cdn) {
        set_do_balance_qty(frm, cdt, cdn)
    }
})

let set_do_balance_qty = function (frm, cdt, cdn) {
    let agent_details = frm.doc.agents_do_detail
    for (let index = 0; index < agent_details.length; index++) {
        if (index == 0) {
            let balance_qty = frm.doc.total_tonnage_mt - agent_details[0].do_received_qty
            frappe.model.set_value(agent_details[0].doctype, agent_details[0].name, "do_balance_qty", balance_qty)
        }
        else {
            let do_balance_qty = agent_details[index - 1].do_balance_qty - agent_details[index].do_received_qty
            frappe.model.set_value(agent_details[index].doctype, agent_details[index].name, "do_balance_qty", do_balance_qty)
        }
    }
    frm.refresh_field("agents_do_detail")
}