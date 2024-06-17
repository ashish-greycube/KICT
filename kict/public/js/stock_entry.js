frappe.ui.form.on("Stock Entry", {
    onload: function(frm){
        frm.set_query("item_code","items", function (doc,cdt,cdn){
            if (frm.doc.stock_entry_type=="Handling Loss" || frm.doc.stock_entry_type=="Audit Shortage" || frm.doc.stock_entry_type=="Cargo Received") {
                return {
                    filters: {
                        is_stock_item: 1,
                        is_customer_provided_item: 1
                    },
                };       
            }

        })

        frm.set_query("custom_vessel", function (doc){
            if (frm.doc.stock_entry_type=="Cargo Received") {
                return {
                    filters: {
                        vessel_closure: 0
                    },
                };       
            }

        })
    }
})