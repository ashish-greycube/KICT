// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Railway Receipt", {
//     onload(frm) {
//         frm.trigger('railway_receipt_on_refresh_load')
//     },
// 	refresh(frm) {
//         frm.trigger('railway_receipt_on_refresh_load')
// 	},

//     railway_receipt_on_refresh_load: function(frm){
//         if (frm.is_new() == undefined) {
//             frm.add_custom_button(__('Delivery Note'), () => create_delivery_note_from_railway_receipt(frm), __("Create"));
//         }
//     }
// });

// function create_delivery_note_from_railway_receipt(frm){
//     if (frm.is_dirty()==true) {
//         frappe.throw({
//             message: __("Please save the form to proceed..."),
//             indicator: "red",
//         });       
//     }

//     frappe.call({
//         method: "kict.kict.doctype.railway_receipt.railway_receipt.create_delivery_note_from_railway_receipt",
//         args: {
//             "source_name": frm.doc.name,
//             "target_doc": undefined,                                        
//             "doctype": frm.doc.doctype
//         },
//         callback: function (response) {
//             if (response.message) {
//                 let url_list = '<a href="/app/delivery-note/' + response.message + '" target="_blank">' + response.message + '</a><br>'
//                 frappe.show_alert({
//                     title: __('Delivery Note is created'),
//                     message: __(url_list),
//                     indicator: 'green'
//                 }, 12);
//                 window.open(`/app/delivery-note/` + response.message);
//             }
//         }
//     });

// }
