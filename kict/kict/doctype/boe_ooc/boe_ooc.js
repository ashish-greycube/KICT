frappe.ui.form.on("BOE OOC", {
    setup(frm) {
        frm.set_query("cargo_name", "boe_ooc_detail", function () {
            if (frm.doc.vessel) {
                return {
                    query: "kict.kict.doctype.boe_ooc.boe_ooc.get_unique_cargo_name",
                    filters: {
                        vessel: frm.doc.vessel
                    },
                };
            }
        });
        frm.set_query("importer_name", function () {
            if (frm.doc.vessel) {
                return {
                    query: "kict.kict.doctype.boe_ooc.boe_ooc.get_unique_customer_name",
                    filters: {
                        vessel: frm.doc.vessel
                    },
                };
            }
        });
    }
});
