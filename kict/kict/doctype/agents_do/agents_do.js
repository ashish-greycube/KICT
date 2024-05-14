frappe.ui.form.on("Agents DO", {
    setup(frm) {
        frm.set_query("importer_name", function () {
            if (frm.doc.vessel) {
                return {
                    query: "kict.kict.doctype.agents_do.agents_do.get_unique_customer_list",
                    filters: {
                        vessel: frm.doc.vessel
                    },
                };
            }
        });

        frm.set_query("item", "agents_do_detail", function () {
            if (frm.doc.vessel) {
                return {
                    query: "kict.kict.doctype.agents_do.agents_do.get_unique_cargo_list",
                    filters: {
                        vessel: frm.doc.vessel
                    },
                };
            }

        });

        frm.set_query("commodity_grade", "agents_do_detail", function () {
            if (frm.doc.vessel) {
                return {
                    query: "kict.kict.doctype.agents_do.agents_do.get_unique_grade_list",
                    filters: {
                        vessel: frm.doc.vessel
                    },
                };
            }
        });
    },
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