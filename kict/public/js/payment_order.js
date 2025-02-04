frappe.ui.form.on("Payment Order", {
    refresh(frm){
        frm.add_custom_button(
            __("Bulk TRFR"),
            () => {
              return frappe.call({
                  method: "kict.api.get_sbi_account_details",
                  args: {
                    docname:frm.doc.name
                  },
                  callback: function (r) {
                    console.log(r.message)
                    function downloadURI(uri, name) 
                    {
                        var link = document.createElement("a");
                        // If you don't know the name or want to use
                        // the webserver default set name = ''
                        link.setAttribute('download', name);
                        link.href = uri;
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                    }                    
                    downloadURI(r.message,"SBI-"+frm.doc.name)
                    }
                })
            },
            __("Download CSV")
          );

          frm.add_custom_button(
            __("Bulk NEFT"),
            () => {
              return frappe.call({
                  method: "kict.api.get_non_sbi_account_details",
                  args: {
                    docname : frm.doc.name
                  },
                  callback: function (r) {
                    console.log(r.message)
                    function downloadURI(uri, name) 
                    {
                        var link = document.createElement("a");
                        // If you don't know the name or want to use
                        // the webserver default set name = ''
                        link.setAttribute('download', name);
                        link.href = uri;
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                    }                    
                    downloadURI(r.message,"Non-SBI-"+frm.doc.name)
                  }
                })
            },
            __("Download CSV")
          );

          frm.add_custom_button(
            __("Statement With Remarks"),
            () => {
              return frappe.call({
                  method: "kict.api.get_statement_with_remarks_data",
                  args: {
                    docname:frm.doc.name
                  },
                  callback: function (r) {
                    console.log(r.message)
                    function downloadURI(uri, name) 
                    {
                        var link = document.createElement("a");
                        // If you don't know the name or want to use
                        // the webserver default set name = ''
                        link.setAttribute('download', name);
                        link.href = uri;
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                    }                    
                    downloadURI(r.message,"Statement-with-remarks-"+frm.doc.name)
                    }
                })
            },
            __("Download CSV")
          );

          frm.add_custom_button(
            __("Invoice Data"),
            () => {
              return frappe.call({
                  method: "kict.api.get_purchase_invoice_data",
                  args: {
                    docname:frm.doc.name
                  },
                  callback: function (r) {
                    console.log(r.message)
                    function downloadURI(uri, name) 
                    {
                        var link = document.createElement("a");
                        // If you don't know the name or want to use
                        // the webserver default set name = ''
                        link.setAttribute('download', name);
                        link.href = uri;
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                    }                    
                    downloadURI(r.message,"Purchase-Invoice-"+frm.doc.name)
                    }
                })
            },
            __("Download CSV")
          );
    }
})