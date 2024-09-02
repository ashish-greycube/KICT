app_name = "kict"
app_title = "Kict"
app_publisher = "GreyCube Technologies"
app_description = "KICT customization"
app_email = "admin@greycube.in"
app_license = "unlicense"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kict/css/kict.css"
# app_include_js = "/assets/kict/js/kict.js"

# include js, css files in header of web template
# web_include_css = "/assets/kict/css/kict.css"
# web_include_js = "/assets/kict/js/kict.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kict/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Item" : "public/js/item.js",
              "Stock Entry" : "public/js/stock_entry.js",
              "Purchase Invoice":"public/js/purchase_invoice.js",
              "Customer":"public/js/customer.js"
              }

# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kict/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

jinja = {
    "methods": [
        "kict.kict.doctype.vessel.vessel.get_item_price",
        "kict.api.get_vessel_grade_details"
    ]
}

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "kict.utils.jinja_methods",
# 	"filters": "kict.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kict.install.before_install"
# after_install = "kict.install.after_install"
after_migrate = "kict.migrate.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "kict.uninstall.before_uninstall"
# after_uninstall = "kict.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kict.utils.before_app_install"
# after_app_install = "kict.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kict.utils.before_app_uninstall"
# after_app_uninstall = "kict.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kict.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Customer": {
		"validate": ["kict.api.set_cargo_handling_option_name_and_is_periodic",
               "kict.api.validate_rate_percent_billing"]
	},
    "Delivery Note": {
        "on_cancel": "kict.api.change_status_for_dn_creation_in_railway_receipt_on_cancel_of_dn",
        "before_validate": "kict.api.validate_vessel_is_not_closed_in_delivery_note",
        "validate":"kict.api.validate_vessel_is_present_in_items"
	},
    "Sales Invoice": {
        "on_cancel": ["kict.api.change_status_for_is_billed_in_on_cancel_of_si",
                      "kict.api.remove_calculation_for_percent_billing_on_cancel_of_si"],
        "on_trash": "kict.api.change_status_for_is_billed_in_on_cancel_of_si",
        "on_submit":"kict.api.set_grt_billed_for_bh_in_vessel_detail_on_submit_of_si"
	},
    "Stock Entry": {
        "before_validate":["kict.api.validate_vessel_is_not_closed_in_stock_entry",
                           "kict.api.validate_items_for_cargoreceived_handlingloss_auditsortage",
                            "kict.api.generate_and_set_batch_no",
                            "kict.api.set_batch_no_and_warehouse_for_handling_loss_audit_sortage"
                           ],
        "validate":"kict.api.validate_vessel_is_present_in_items"                                  
	},
    "Sales Order": {
        "on_submit":"kict.api.set_grt_billed_for_bh_in_vessel_detail_on_submit_of_pi",
        "on_cancel":"kict.api.remove_calculation_for_percent_billing_on_cancel_of_pi"
    }        
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"kict.tasks.all"
# 	],
# 	"daily": [
# 		"kict.tasks.daily"
# 	],
# 	"hourly": [
# 		"kict.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kict.tasks.weekly"
# 	],
# 	"monthly": [
# 		"kict.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "kict.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kict.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kict.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kict.utils.before_request"]
# after_request = ["kict.utils.after_request"]

# Job Events
# ----------
# before_job = ["kict.utils.before_job"]
# after_job = ["kict.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"kict.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

