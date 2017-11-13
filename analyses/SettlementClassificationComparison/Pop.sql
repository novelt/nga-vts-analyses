
/*
 select zt9.sum / 100 as "total 9x9", zu9.sum / (100 * 1000000) as "Under 5 9x9", zt90.sum AS "Total 90x90", zu90.sum / 1000000 AS "Under 5 90x90", 
zt9.count, 
--zu9.count, 
zt90.count, 
--zu90.count,
 scb.* FROM   postgis.ward_settlement_classification_blocks scb
 left join zonalstats_total_90by90 zt90 on zt90.id = scb.id
 left join zonalstats_total_9by9 zt9 on zt9.id = scb.id
 left join zonalstats_under5_90by90 zu90 on zu90.id = scb.id
 left join zonalstats_under5_9by9 zu9 on zu9.id = scb.id
 */
 --where id < 5



select SUM(zt9.sum / 100) as "Total Population", 
SUM(zu9.sum / (100 * 1000000)) as "Under 5 Population",
scb.ward_name, scb.lga_name, scb.state_name, scb.type, scb.handmade_etally_ward
FROM 
	postgis.ward_settlement_classification_blocks scb
	left join zonalstats_total_9by9 zt9 on zt9.id = scb.id
	left join zonalstats_under5_9by9 zu9 on zu9.id = scb.id
GROUP BY scb.ward_name, scb.lga_name, scb.state_name, scb.type, scb.handmade_etally_ward
order by state_name, lga_name, ward_name, type
;