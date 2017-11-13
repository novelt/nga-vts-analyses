COPY 
(
select c.campaignId as "Campaign Id", 
c.campaignLabel AS "Campaign Label",
ga.stateCode as "State Code",
ga.stateName as "State Name",
ga.lgacode as "LGA Code",
ga.lganame as "LGA Name",
ta.wardCode as "Ward Code",
ga.wardName as "Ward Name" from vts_campaignTargetedAreas ta
inner join vts_campaigns c ON c.campaignid = ta.campaignid
inner join vts_dim_geo_admin ga on ga.wardcode = ta.wardcode
where  exists (select 1 from postgis.vts_tally_fact tf where tf.campaign_id = ta.campaignId and tf.ward_code = ga.wardCode)
order by c.startDate, ga.statename, ga.lganame, ga.wardname
)
TO 'D:\git\vts\src\esri\scripts\OrnlAndEtallyComparison\targeted_etally.csv' WITH CSV HEADER;