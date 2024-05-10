// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rake Dispatch", {
	setup(frm) {
        frm.set_query("grade", "rake_prelim_entry", function(doc,cdt,cdn){
            let unique_grade_list=[]
            let row = locals[cdt][cdn]
            let details = frm.doc.rake_prelim_entry
            frappe.db.get_list("Vessel Details",{
                parent_doctype:"Vessel",
                filters:{
                    "parent" : row.vcn_no
                },
                fields:["grade"] 
            }).then(grades => {
                if(grades.length > 0){
                    let grade_list = []
                    grades.forEach(r => {
                        grade_list.push(r.grade)
                    });
        
                    unique_grade_list = [...new Set(grade_list)]
        
                    console.log('unique_grade_list',unique_grade_list)
                        return {
                            filters: {
                                name: ["in", unique_grade_list]
                            }
                        }
                   
                }
            })
        });
	},
});
// frappe.ui.form.on("Rake Prelim Entry", {
//     vcn_no(frm, cdt, cdn) {
//         let row = locals[cdt][cdn]
//         let details = frm.doc.rake_prelim_entry
//         frappe.db.get_list("Vessel Details",{
//             parent_doctype:"Vessel",
//             filters:{
//                 "parent" : row.vcn_no
//             },
//             fields:["grade"] 
//         }).then(grades => {
//             if(grades.length > 0){
//                 let grade_list = []
//                 grades.forEach(r => {
//                     grade_list.push(r.grade)
//                 });
    
//                 let unique_grade_list = [...new Set(grade_list)]
    
//                 frm.set_query("grade", "rake_prelim_entry", function(){
//                     return {
//                         filters: {
//                             name: ["in", unique_grade_list]
//                         }
//                     }
//                 });
//             }
//         })
//     }
// });