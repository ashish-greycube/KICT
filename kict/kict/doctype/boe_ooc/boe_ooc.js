frappe.ui.form.on("BOE OOC", {
    onload(frm) {
        frm.trigger("cargo_and_customer_filter")
    },
    vessel(frm) {
        frm.trigger("cargo_and_customer_filter")
    },
    cargo_and_customer_filter:  function (frm) {
            frappe.db.get_list("Vessel Details", {
                parent_doctype: "Vessel",
                filters: {
                    "parent": frm.doc.vessel
                },
                fields: ["commodity", "customer_name"]
            }).then(records => {
                let cargo_commodity = [];
                let customer = [];
                records.forEach(values => {
                    cargo_commodity.push(values.commodity)
                    customer.push(values.customer_name)
                })
                let unique_commodity = [...new Set(cargo_commodity)];
                let unique_customer = [...new Set(customer)];

                frm.set_query("cargo_name","boe_ooc_detail", function(){
                    let return_filters = {}
                    if(frm.doc.vessel){
                        return_filters["item_code"]= ["in", unique_commodity]
                    }
                    else{
                        return_filters["item_code"]=["in", '']
                    }
                    return {
                        filters:return_filters
                    }
                });
                
                frm.set_query("importer_name", function(){
                    let return_filters = {}
                    if(frm.doc.vessel){
                        return_filters["name"]= ["in", unique_customer]
                    }
                    else{
                        return_filters["name"]=["in", '']
                    }
                    return {
                        filters:return_filters
                    }
                })
            })
        }
});
