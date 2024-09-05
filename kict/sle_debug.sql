with fn as
(
	select tsle.name , tsle.vessel , posting_datetime , tb.item , tsle.posting_date , 
	tb.manufacturing_date , voucher_type , voucher_no , serial_and_batch_bundle , tsabe.batch_no ,
	tse.stock_entry_type
	from `tabStock Ledger Entry` tsle 
	inner join `tabSerial and Batch Entry` tsabe on tsabe.parent = tsle.serial_and_batch_bundle 
	inner join tabBatch tb on tb.name = tsabe.batch_no 
	left outer join `tabStock Entry` tse on tse.name = tsle.voucher_no
	where actual_qty < 0 
-- 	and tsle.vessel like 'MV YARRA STAR-20240806'
)
select 
distinct a.vessel , a.item , a.voucher_type , a.stock_entry_type ,
a.posting_date , b.posting_date b_posting_date, 
a.batch_no , b.batch_no b_batch_no,
a.manufacturing_date , b.manufacturing_date b_manufacturing_date
from fn a
inner join fn b on a.name <> b.name
and a.vessel = b.vessel
and a.item = b.item
and a.batch_no <> b.batch_no
and b.posting_date > a.posting_date and b.manufacturing_date < a.manufacturing_date
-- group by a.vessel , a.item , a.batch_no , a.posting_date
order by a.posting_datetime