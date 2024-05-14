import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def after_migrate():
    custom_data_creation()
    # custom_field_creation()

def custom_data_creation() :
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



def custom_field_creation():
    custom_fields = {
        "Item": [
            {
				"fieldname":"custom_customer_abbreviation",
				"label":"Customer Abbreviation",
				"fieldtype":"Data",
				"insert_after": "customer",
				"is_custom_field":1,
				"is_system_generated":0,
                "fetch_from": "customer.custom_customer_abbreviation",
            },
            {
				"fieldname":"custom_coal_commodity",
				"label":"Coal Commodity",
				"fieldtype":"Link",
                "options": "Coal Commodity",
				"insert_after": "custom_customer_abbreviation",
				"is_custom_field":1,
				"is_system_generated":0,
            },
            {
				"fieldname":"custom_commodity_grade",
				"label":"Grade",
				"fieldtype":"Link",
                "options": "Commodity Grade",
				"insert_after": "custom_coal_commodity",
				"is_custom_field":1,
				"is_system_generated":0,
            }  

        ],
        "Customer": [
            {
				"fieldname":"custom_customer_abbreviation",
				"label":"Customer Abbreviation",
				"fieldtype":"Data",
				"insert_after": "customer_group",
				"is_custom_field":1,
				"is_system_generated":0,
            }
        ]        
    }

    for dt, fields in custom_fields.items():
        print("*******\n %s: " % dt, [d.get("fieldname") for d in fields])
    create_custom_fields(custom_fields)

    