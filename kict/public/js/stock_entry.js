frappe.ui.form.on("Stock Entry", {
    stock_entry_type:function(frm){
        set_display_required_for_vessel_field(frm,filter_item=true)
    },
    setup: function(frm){
        set_display_required_for_vessel_field(frm,filter_item=true)
        // frm.set_query("item_code","items", function (doc,cdt,cdn){
            // if (frm.doc.stock_entry_type=="Handling Loss" || frm.doc.stock_entry_type=="Audit Shortage" || frm.doc.stock_entry_type=="Cargo Received") {
                // return {
                //     query: "kict.api.set_query_for_item_based_on_stock_entry_type",
                //     filters: {
                //         is_stock_item: 1,
                //         is_customer_provided_item: 1
                //     },
                // };       
            // }

        // })

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

function set_display_required_for_vessel_field(frm,filter_item=false) {
    if (filter_item == true){
        debugger
        frm.set_query("item_code","items", function (frm,cdt,cdn){
            frappe.db.get_value('Coal Settings', 'Coal Settings', ['cargo_received', 'handling_loss','audit_shortage'])
            .then(r => {
                let values = r.message;
                if (frm.doc.stock_entry_type==values.cargo_received || frm.doc.stock_entry_type==values.handling_loss || frm.doc.stock_entry_type==values.audit_shortage) {
                    return {
                        filters: {
                            is_stock_item: 1,
                            is_customer_provided_item: 1
                        },
                    };       
                }                
            
                frm.set_query("custom_vessel", function (frm){
                    if (frm.doc.stock_entry_type==values.cargo_received || frm.doc.stock_entry_type==values.handling_loss || frm.doc.stock_entry_type==values.audit_shortage) {
                        return {
                            filters: {
                                vessel_closure: 0
                            },
                        };       
                    }
        
                })
            })


        })

    }    
    if (frm.doc.stock_entry_type) {
        frappe.db.get_value('Coal Settings', 'Coal Settings', ['cargo_received', 'handling_loss','audit_shortage'])
        .then(r => {
            let values = r.message;
            if (frm.doc.stock_entry_type==values.cargo_received || frm.doc.stock_entry_type==values.handling_loss || frm.doc.stock_entry_type==values.audit_shortage) {
                frm.set_df_property('custom_vessel','hidden',0)
                frm.set_df_property('custom_vessel','reqd',1)
            }else{
                frm.set_df_property('custom_vessel','hidden',1)
                frm.set_df_property('custom_vessel','reqd',0)
            }

        })
        
    }else{
        frm.set_df_property('custom_vessel','hidden',1)
        frm.set_df_property('custom_vessel','reqd',0)       
    }   
}