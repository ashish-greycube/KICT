frappe.ui.form.on('Item', {
    is_customer_provided_item: function(frm) {
		frm.trigger('set_item_name_for_customer_provided_item')
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
        if (frm.is_new()==1 && frm.doc.is_customer_provided_item==1) {
            let auto_item_name=[]
            if (frm.doc.custom_customer_abbreviation) {
                auto_item_name.push(frm.doc.custom_customer_abbreviation)
            }
            if (frm.doc.custom_coal_commodity) {
                auto_item_name.push(frm.doc.custom_coal_commodity)
            }     
            if (frm.doc.custom_commodity_grade) {
                auto_item_name.push(frm.doc.custom_commodity_grade)
            }      
            let proposed_name=auto_item_name.join('_')       
            frm.set_value('item_code',proposed_name)
            frm.set_value('item_name',proposed_name)
        }

    }
});