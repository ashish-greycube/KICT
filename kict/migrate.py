import frappe

def after_migrate():
    naming_rule = frappe.db.get_list(
        "Document Naming Rule", filters={"document_type": "Vessel Details"})
    
    if(len(naming_rule) < 1):
        print("New doc Vessel Details is created in Document naming rule")
        doc = frappe.new_doc('Document Naming Rule')
        doc.document_type = "Vessel Details"
        doc.prefix = "BL-"
        doc.prefix_digits = 1
        doc.priority = 0
        doc.insert()

    else:
        print("Vessel Details doc is already exist in Document namin rule")