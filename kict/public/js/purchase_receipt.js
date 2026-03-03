frappe.ui.form.on("Purchase Receipt", {
    onload(frm) {
        let logged_in_user_roles = frappe.user_roles
        console.log(logged_in_user_roles)
        if (logged_in_user_roles.length > 0){
            logged_in_user_roles.forEach(element => {
                if (element.includes("Verifier")) {
                    frm.set_df_property("custom_packing_condition", "reqd", 1);
                    frm.set_df_property("custom_surface_finish", "reqd", 1);
                    frm.set_df_property("custom_physical_damage", "reqd", 1);
                }
            });
        } 
    }
})