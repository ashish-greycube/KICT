// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Rake Dispatch", {
// 	refresh(frm) {

// 	},
// });
// frappe.ui.form.on("Rake Prelim Entry", {
//     vcn_no(frm, cdt, cdn) {
//         let row = locals[cdt][cdn]
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
//                     // let return_filters = {}
//                     // if(grades.vcn_no){
//                     //     return_filters["name"]= ["in", unique_grade_list]
//                     // }
//                     // else{
//                     //     return_filters["name"]=["in", '']
//                     // }
//                     // return {
//                     //     filters:return_filters
//                     // }
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