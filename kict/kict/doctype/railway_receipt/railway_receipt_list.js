frappe.listview_settings['Railway Receipt'] = {
    onload: function (listview) {
        listview.page.add_menu_item(__("<b>Submit RR</b>"), function () {
        //   let items = listview.get_checked_items(true);
            frappe.call({
                method: "kict.kict.doctype.railway_receipt.railway_receipt.submit_bulk_railway_receipts", 
                freeze: true,
                freeze_message: "Processing...",
                // args: undefined,
                callback: function(r) {
                    console.log(r)
                }
            });            
        });
      },
}