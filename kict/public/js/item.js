frappe.ui.form.on('Item', {
    is_customer_provided_item: function(frm) {
		frm.trigger('set_item_name_for_customer_provided_item')
        frm.trigger('set_stock_uom_for_customer_provided_item')
	},
	custom_customer_abbreviation: function(frm) {
		frm.trigger('set_item_name_for_customer_provided_item')
	},
	custom_coal_commodity: function(frm) {
		frm.trigger('set_item_name_for_customer_provided_item')
	},
	custom_commodity_grade: function(frm) {
		frm.trigger('set_item_name_for_customer_provided_item')
	},    

    set_item_name_for_customer_provided_item(frm){
        debugger
        if (frm.is_new()==1 && frm.doc.is_customer_provided_item==1) {
            let auto_item_name=[]
            if (frm.doc.custom_coal_commodity) {
                auto_item_name.push(frm.doc.custom_coal_commodity)
            }     
            if (frm.doc.custom_commodity_grade) {
                auto_item_name.push(frm.doc.custom_commodity_grade)
            }      
            if (frm.doc.custom_customer_abbreviation) {
                auto_item_name.push(frm.doc.custom_customer_abbreviation)
            }
            let proposed_name=auto_item_name.join('_')       
            frm.set_value('item_code',proposed_name)
            frm.set_value('item_name',proposed_name)
        }

    },
    set_stock_uom_for_customer_provided_item(frm){
        if (frm.is_new()==1 && frm.doc.is_customer_provided_item==1) {
            let default_uom_for_cargo = frappe.db.get_single_value("Coal Settings","default_uom_for_cargo")
            .then(response => {
                frm.set_value("stock_uom",response)
                frappe.show_alert({
                    message:__('Default Uom of item is set to {0}',[response]),
                    indicator:'green'
                }, 5);
            })
        }
    }
});