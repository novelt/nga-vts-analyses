begin;


DROP TABLE IF EXISTS public.pop_comparison;
CREATE TABLE public.pop_comparison
(
	id serial,
	campaign_id int,
	settlement_type varchar,
	denom_objectid int,
	denom_globalid uuid,
	settlement_objectid int,
	settlement_globalid uuid,
	settlement_settlementobjectid varchar,
	ward_code varchar,
	etally_pop int,
	non_adjusted_pop double precision,
	adjusted_pop double precision,
	settlement_non_adjusted_pop double precision,
	settlement_adjusted_pop double precision,
	UNIQUE(campaign_id, denom_globalid),
	UNIQUE(campaign_id, settlement_type, denom_objectid)	
);

CREATE INDEX pop_comparison_settlement_settlementObjectID_idx
  ON public.pop_comparison
  USING btree
  (settlement_settlementObjectID);

commit;
begin;

DELETE FROM public.pop_comparison
WHERE settlement_type = 'SSA';

INSERT INTO public.pop_comparison
(
	campaign_id,
	settlement_type,
	settlement_objectid,
	settlement_globalid,
	settlement_settlementobjectid,
	denom_objectid,
	denom_globalid,
	ward_code,
	etally_pop
)
SELECT 
	fact.campaign_id,
	'SSA' ,
	f.objectid as settlement_objectid,
	f.globalid as settlement_globalid,
	f.settlementObjectId as settlement_settlementobjectid,
	d.objectid as denom_objectid,
	d.globalid as denom_globalid ,
	f.wardCode as ward_code,
	COALESCE(SUM(fact.household_eligible), 0)
	AS etally_pop
FROM 
postgis.FE_SmlSettlementAreas f 
LEFT JOIN postgis.vts_gpreflyrssabuffers d on f.globalid = d.settlementGuid
INNER JOIN postgis.vts_tally_fact fact ON ST_Intersects(f.shape, fact.shape)
--ignore revisits and outside vaccinations
WHERE fact.revisit_type IS NULL
AND COALESCE(fact.outside_vaccinated, 0) <= 0
GROUP BY
	fact.campaign_id,
	f.objectid,
	d.objectid,
	f.settlementObjectId,
	f.wardCode;

commit;
begin;

--SSA non adjusted denominator population


UPDATE public.pop_comparison 
SET non_adjusted_pop = COALESCE(zs1.sum,0)+
	COALESCE(zs2.sum,0)+
	COALESCE(zs3.sum, 0) +
	COALESCE(zs4.sum, 0),
    settlement_non_adjusted_pop = COALESCE(zs1.sum,0)+
	COALESCE(zs2.sum,0)+
	COALESCE(zs3.sum, 0) +
	COALESCE(zs4.sum, 0)
FROM 
	zonalstats_0_0_f_ssa zs1 
	LEFT JOIN zonalstats_0_0_m_ssa zs2 ON zs1.objectid_1 = zs2.objectid_1
	LEFT JOIN zonalstats_1_4_f_ssa zs3 ON zs1.objectid_1 = zs3.objectid_1
	LEFT JOIN zonalstats_1_4_m_ssa zs4 ON zs1.objectid_1 = zs4.objectid_1
WHERE
	zs1.objectid_1 = pop_comparison.settlement_objectid AND 
	pop_comparison.settlement_type = 'SSA';

commit;
begin;

--SSA adjusted pop

UPDATE public.pop_comparison AS pop_comp
SET 
    adjusted_pop = pop.value,
    settlement_adjusted_pop = pop.value
FROM 
	postgis.vts_populationEstimates pop 
WHERE 
	pop.globalid = pop_comp.settlement_globalid
	AND pop.gender = 'MF' 
	AND pop_comp.settlement_type = 'SSA'
	AND pop.age_group_from = 0 and pop.age_group_to = 4
	AND pop.fcname = 'FE_SmlSettlementAreas';

commit;
begin;

INSERT INTO public.pop_comparison
(
	campaign_id,
	settlement_type,
	settlement_objectid,
	settlement_globalid,
	
	denom_objectid,
	denom_globalid,
	settlement_settlementobjectid,
	ward_code,
	etally_pop
)
SELECT 
	fact.campaign_id,
	'BUA' ,
	set.objectid,
	set.globalid,
	f.objectid as denom_objectid,
	f.globalid as denom_globalid,
	f.settlementObjectId as settlement_settlementobjectid,
	f.wardCode as ward_code,
	COALESCE(SUM(fact.household_eligible), 0)
	
	AS etally_pop
FROM postgis.vts_gpreflyrbuagrids f 
INNER JOIN postgis.fe_builtUpArea set on set.globalid = f.settlementGuid
INNER JOIN postgis.vts_tally_fact fact ON ST_Intersects(f.shape, fact.shape)
WHERE fact.revisit_type IS NULL
AND COALESCE(fact.outside_vaccinated, 0) <= 0
GROUP BY
	fact.campaign_id,
	f.objectid,
	f.settlementObjectId,
	set.objectid,
	f.wardCode;

commit;	
begin;

UPDATE public.pop_comparison AS pop_comp
SET non_adjusted_pop = COALESCE(zs1.sum,0)+
	COALESCE(zs2.sum,0)+
	COALESCE(zs3.sum, 0) +
	COALESCE(zs4.sum, 0)
FROM 
	zonalstats_0_0_f_gridcells zs1 
	LEFT JOIN zonalstats_0_0_m_gridcells zs2 ON zs1.objectid_1 = zs2.objectid_1
	LEFT JOIN zonalstats_1_4_f_gridcells zs3 ON zs1.objectid_1 = zs3.objectid_1
	LEFT JOIN zonalstats_1_4_m_gridcells zs4 ON zs1.objectid_1 = zs4.objectid_1
WHERE
	zs1.objectid_1 = pop_comp.denom_objectid
	AND pop_comp.settlement_type = 'BUA';

commit;
begin;

UPDATE public.pop_comparison AS pop_comp
SET 
    adjusted_pop = pop.value
FROM 
	postgis.vts_populationEstimates pop 
WHERE 
	pop.globalid = pop_comp.denom_globalid
	AND pop.gender = 'MF' 
	AND pop_comp.settlement_type = 'BUA'
	AND pop.age_group_from = 0 and pop.age_group_to = 4
	AND pop.fcname = 'VTS_GPRefLyrBUAGrids';
	
commit;
begin;

DELETE FROM public.pop_comparison where settlement_type = 'HA';
	
INSERT INTO public.pop_comparison
(
	campaign_id,
	settlement_type,
	settlement_objectid,
	settlement_globalid,
	settlement_settlementobjectid,
	denom_objectid,
	denom_globalid,
	ward_code,
	etally_pop
)
SELECT 
	
	fact.campaign_id,
	'HA',
	f.objectid as settlement_objectid,
	f.globalid as settlement_globalid,
	f.settlementObjectId as settlement_settlementobjectid,
	d.objectid as denom_objectid,
	d.globalid as denom_globalid,	
	f.wardCode as ward_code,
	COALESCE(SUM(fact.household_eligible), 0)
	AS etally_pop
FROM postgis.FE_HamletAreas f INNER JOIN 
	postgis.vts_tally_fact fact ON ST_Intersects(f.shape, fact.shape)
	LEFT JOIN postgis.etally_raw_data rd on rd.id = fact.id
	LEFT JOIN TallyNearTable nt ON nt.in_fid = rd.objectid
	LEFT JOIN postgis.VTS_GPRefLyrHABuffers d on d.objectid = nt.near_fid
WHERE fact.revisit_type IS NULL	
    AND COALESCE(fact.outside_vaccinated, 0) <= 0
    --This is needed because hamlet areas can be on one another so we use the near tables denominator to decide who wins
	AND d.settlementGuid = f.globalid
GROUP BY 
	fact.campaign_id,
	f.objectid,
	f.settlementObjectId,
	d.objectid,
	f.wardCode;


commit;

--Create a ha helper table.  Will need to know total population in order to know ratio
CREATE OR REPLACE FUNCTION create_pop_ha_helper()

RETURNS void AS
$BODY$
BEGIN

DROP TABLE IF EXISTS public.pop_ha_helper;

CREATE TABLE public.pop_ha_helper
(
	id serial PRIMARY KEY,
	unadjusted_settlement_pop double precision NOT NULL,
	unadjusted_total_denom_pop  double precision ,
	adjusted_settlement_pop double precision ,
	adjusted_total_denom_pop  double precision ,
	globalid uuid NOT NULL,
	objectid int NOT NULL,
	settlementObjectId varchar NOT NULL UNIQUE,
	missing_raw boolean
);


INSERT INTO public.pop_ha_helper
(settlementObjectId, objectid, globalid, unadjusted_settlement_pop, missing_raw)
SELECT DISTINCT f.settlementObjectId, f.objectid, f.globalid, COALESCE(zs1.sum,0)+
	COALESCE(zs2.sum,0)+
	COALESCE(zs3.sum, 0) +
	COALESCE(zs4.sum, 0)  AS unadjusted_ha_pop,
	zs1.objectid_1 IS NULL AS missing_raw 
FROM 
	postgis.FE_HamletAreas f
	INNER JOIN pop_comparison ON f.globalid = pop_comparison.settlement_globalid AND pop_comparison.settlement_type = 'HA'
	LEFT JOIN zonalstats_0_0_f_ha zs1 ON zs1.objectid_1 = f.objectid
	LEFT JOIN zonalstats_0_0_m_ha zs2 ON zs1.objectid_1 = zs2.objectid_1
	LEFT JOIN zonalstats_1_4_f_ha zs3 ON zs1.objectid_1 = zs3.objectid_1
	LEFT JOIN zonalstats_1_4_m_ha zs4 ON zs1.objectid_1 = zs4.objectid_1;

/*
CREATE TABLE zonalstats_0_0_f_hamlets AS
(
SELECT * FROM zonalstats_0_0_f_hamlets_0
UNION ALL
SELECT * FROM zonalstats_0_0_f_hamlets_1
UNION ALL
SELECT * FROM zonalstats_0_0_f_hamlets_2
UNION ALL
SELECT * FROM zonalstats_0_0_f_hamlets_3
UNION ALL
SELECT * FROM zonalstats_0_0_f_hamlets_4
);

CREATE TABLE zonalstats_0_0_m_hamlets AS
(
SELECT * FROM zonalstats_0_0_m_hamlets_0
UNION ALL
SELECT * FROM zonalstats_0_0_m_hamlets_1
UNION ALL
SELECT * FROM zonalstats_0_0_m_hamlets_2
UNION ALL
SELECT * FROM zonalstats_0_0_m_hamlets_3
UNION ALL
SELECT * FROM zonalstats_0_0_m_hamlets_4
);



CREATE TABLE zonalstats_0_0_f_hamlets AS
(
SELECT * FROM zonalstats_0_0_f_hamlets_0
UNION ALL
SELECT * FROM zonalstats_0_0_f_hamlets_1
UNION ALL
SELECT * FROM zonalstats_0_0_f_hamlets_2
UNION ALL
SELECT * FROM zonalstats_0_0_f_hamlets_3
UNION ALL
SELECT * FROM zonalstats_0_0_f_hamlets_4
);

CREATE TABLE zonalstats_0_0_m_hamlets AS
(
SELECT * FROM zonalstats_0_0_m_hamlets_0
UNION ALL
SELECT * FROM zonalstats_0_0_m_hamlets_1
UNION ALL
SELECT * FROM zonalstats_0_0_m_hamlets_2
UNION ALL
SELECT * FROM zonalstats_0_0_m_hamlets_3
UNION ALL
SELECT * FROM zonalstats_0_0_m_hamlets_4
);


CREATE TABLE zonalstats_1_4_f_hamlets AS
(
SELECT * FROM zonalstats_1_4_f_hamlets_0
UNION ALL
SELECT * FROM zonalstats_1_4_f_hamlets_1
UNION ALL
SELECT * FROM zonalstats_1_4_f_hamlets_2
UNION ALL
SELECT * FROM zonalstats_1_4_f_hamlets_3
UNION ALL
SELECT * FROM zonalstats_1_4_f_hamlets_4
);

CREATE TABLE zonalstats_1_4_m_hamlets AS
(
SELECT * FROM zonalstats_1_4_m_hamlets_0
UNION ALL
SELECT * FROM zonalstats_1_4_m_hamlets_1
UNION ALL
SELECT * FROM zonalstats_1_4_m_hamlets_2
UNION ALL
SELECT * FROM zonalstats_1_4_m_hamlets_3
UNION ALL
SELECT * FROM zonalstats_1_4_m_hamlets_4
);
*/


UPDATE pop_ha_helper
SET unadjusted_total_denom_pop = sq.total
FROM 
(
SELECT
	d.settlementguid,
	COALESCE(SUM(zd1.sum), 0)
	+ COALESCE(SUM(zd2.sum), 0)
	+ COALESCE(SUM(zd3.sum), 0) 
	+ COALESCE(SUM(zd4.sum), 0) as total
FROM 
	postgis.VTS_GPRefLyrHABuffers d 
	LEFT JOIN zonalstats_0_0_f_hamlets zd1 ON zd1.objectid_1 = d.objectid
	LEFT JOIN zonalstats_0_0_m_hamlets zd2 ON zd1.objectid_1 = zd2.objectid_1
	LEFT JOIN zonalstats_1_4_f_hamlets zd3 ON zd1.objectid_1 = zd3.objectid_1
	LEFT JOIN zonalstats_1_4_m_hamlets zd4 ON zd1.objectid_1 = zd4.objectid_1
GROUP BY d.settlementguid
) sq
WHERE sq.settlementGuid = pop_ha_helper.globalid;


UPDATE pop_ha_helper
SET adjusted_total_denom_pop = 
(SELECT
	SUM(value)
FROM 
	postgis.VTS_GPRefLyrHABuffers d 
	LEFT JOIN postgis.vts_populationEstimates pop ON pop.globalid = d.globalid
WHERE 
	d.settlementGuid = pop_ha_helper.globalid
	AND pop.gender = 'MF' 	
	AND pop.age_group_from = 0 
	AND pop.age_group_to = 4
	AND pop.fcname = 'VTS_GPRefLyrHABuffers'
);


UPDATE pop_ha_helper
SET adjusted_settlement_pop = 
(SELECT
	SUM(value)
FROM 
	postgis.vts_populationEstimates pop 
WHERE 
	pop.globalid = pop_ha_helper.globalid
	AND pop.gender = 'MF' 	
	AND pop.age_group_from = 0 
	AND pop.age_group_to = 4
	AND pop.fcname = 'FE_HamletAreas');


END;
$BODY$
LANGUAGE plpgsql VOLATILE;


begin;

UPDATE public.pop_comparison
SET non_adjusted_pop = ph.unadjusted_settlement_pop * ( (COALESCE(zd1.sum, 0)
	+ COALESCE(zd2.sum, 0)
	+ COALESCE(zd3.sum, 0) 
	+ COALESCE(zd4.sum, 0) ) / ph.unadjusted_total_denom_pop )
FROM pop_ha_helper ph,  
	zonalstats_0_0_f_hamlets zd1 
	LEFT JOIN zonalstats_0_0_m_hamlets zd2 ON zd1.objectid_1 = zd2.objectid_1
	LEFT JOIN zonalstats_1_4_f_hamlets zd3 ON zd1.objectid_1 = zd3.objectid_1
	LEFT JOIN zonalstats_1_4_m_hamlets zd4 ON zd1.objectid_1 = zd4.objectid_1
	
WHERE pop_comparison.settlement_globalid = ph.globalid
	AND zd1.objectid_1 = pop_comparison.denom_objectid
	AND pop_comparison.settlement_type = 'HA'
	AND ph.unadjusted_total_denom_pop > 0;

commit;
begin;
--Update HA adjusted using proportion of non adjusted denom / total non adjusted denom as ratio

UPDATE public.pop_comparison
SET adjusted_pop = ph.adjusted_settlement_pop * ( (COALESCE(zd1.sum, 0)
	+ COALESCE(zd2.sum, 0)
	+ COALESCE(zd3.sum, 0) 
	+ COALESCE(zd4.sum, 0) ) / ph.unadjusted_total_denom_pop )
FROM pop_ha_helper ph,  
	zonalstats_0_0_f_hamlets zd1 
	LEFT JOIN zonalstats_0_0_m_hamlets zd2 ON zd1.objectid_1 = zd2.objectid_1
	LEFT JOIN zonalstats_1_4_f_hamlets zd3 ON zd1.objectid_1 = zd3.objectid_1
	LEFT JOIN zonalstats_1_4_m_hamlets zd4 ON zd1.objectid_1 = zd4.objectid_1
	
WHERE pop_comparison.settlement_globalid = ph.globalid
	AND pop_comparison.settlement_type = 'HA'
	AND zd1.objectid_1 = pop_comparison.denom_objectid
	AND ph.unadjusted_total_denom_pop > 0;

commit;
begin;
--Update HA settlement non adjusted 

UPDATE  public.pop_comparison
SET settlement_non_adjusted_pop = COALESCE(zs1.sum,0)+
	COALESCE(zs2.sum,0)+
	COALESCE(zs3.sum, 0) +
	COALESCE(zs4.sum, 0)
FROM 
	zonalstats_0_0_f_ha zs1 
	LEFT JOIN zonalstats_0_0_m_ha zs2 ON zs1.objectid_1 = zs2.objectid_1
	LEFT JOIN zonalstats_1_4_f_ha zs3 ON zs1.objectid_1 = zs3.objectid_1
	LEFT JOIN zonalstats_1_4_m_ha zs4 ON zs1.objectid_1 = zs4.objectid_1
WHERE settlement_type = 'HA' AND pop_comparison.settlement_objectid = zs1.objectid_1;

commit;
begin;

--Bua settlement non adjusted pop

UPDATE  public.pop_comparison
SET settlement_non_adjusted_pop = COALESCE(zs1.sum,0)+
	COALESCE(zs2.sum,0)+
	COALESCE(zs3.sum, 0) +
	COALESCE(zs4.sum, 0)
FROM 
	zonalstats_0_0_f_bua zs1 
	LEFT JOIN zonalstats_0_0_m_bua zs2 ON zs1.objectid_1 = zs2.objectid_1
	LEFT JOIN zonalstats_1_4_f_bua zs3 ON zs1.objectid_1 = zs3.objectid_1
	LEFT JOIN zonalstats_1_4_m_bua zs4 ON zs1.objectid_1 = zs4.objectid_1
WHERE settlement_type = 'BUA' AND pop_comparison.settlement_objectid = zs1.objectid_1;

commit;
begin;

UPDATE pop_comparison
SET settlement_adjusted_pop = pop.value
FROM 
	postgis.vts_populationEstimates pop 
WHERE 
	pop.globalid = pop_comparison.settlement_globalid
	AND pop.featureIdentifier = pop_comparison.settlement_settlementObjectID
	AND pop.gender = 'MF' 	
	AND pop.age_group_from = 0 
	AND pop.age_group_to = 4;

commit;


/*
'VTS_GPRefLyrSSABuffers'
'FE_SmlSettlementAreas'
'FE_BuiltUpArea'
'Boundary_VaccWards'
'Boundary_VaccStates'
'Boundary_VaccLGAs'
'VTS_GPRefLyrHABuffers'
'FE_HamletAreas'
'VTS_GPRefLyrBUAGrids'


select 
ds.GeoZone AS "GeoZone",
ds.StateCode AS "StateCode",
ds.StateName AS "StateName",
ds.LGACode AS "LGACode",
ds.LGAName AS "LGAName",
ds.WardCode AS "WardCode",
ds.WardName AS "WardName",
ds.SettlementObjectId AS "SettlementObjectId",
ds.SettlementName AS "SettlementName",
ds.SettlementType AS "SettlementType",
ds.TotalFeatures AS "Nbdenominator",
ds.Weight AS "Weight",
* from public.vts_dim_settlements ds
limit 10;*/





COPY (
	
select ds.stateName, ds.stateCode, ds.geoZone, ds.lganame, ds.lgacode, ds.lgaAmapCode, ds.wardname, ds.wardcode,
 ds.settlementType, ds.settlementName, ds.settlementObjectId, ds.totalFeatures, 
pc.campaign_id, 
c.campaignLabel,
pc.settlement_adjusted_pop,
pc.settlement_non_adjusted_pop,
sum(pc.adjusted_pop) as "Population of visited denominators (adjusted)",
sum(pc.non_adjusted_pop) as "Population of visited denominators (unadjusted)",
count(denom_globalid) AS "Visited Denominators",
100.0 * count(denom_globalid)::float / ds.totalFeatures AS "E-Tally Coverage %",
CASE 
	WHEN (100.0 * ( ( 5 * count(denom_globalid) ) / ds.totalFeatures)::int / 5.0)::int = 0 THEN '0-19%' 
	WHEN (100.0 * ( ( 5 * count(denom_globalid) ) / ds.totalFeatures)::int / 5.0)::int = 20 THEN '20-39%' 
	WHEN (100.0 * ( ( 5 * count(denom_globalid) ) / ds.totalFeatures)::int / 5.0)::int = 40 THEN '40-59%' 
	WHEN (100.0 * ( ( 5 * count(denom_globalid) ) / ds.totalFeatures)::int / 5.0)::int = 60 THEN '60-79%' 
	WHEN (100.0 * ( ( 5 * count(denom_globalid) ) / ds.totalFeatures)::int / 5.0)::int = 80 THEN '80-99%' 
	WHEN (100.0 * ( ( 5 * count(denom_globalid) ) / ds.totalFeatures)::int / 5.0)::int = 100 THEN '100%' 
	ELSE '?%'
END
	AS "E-Tally Coverage % Rounded",
sum(etally_pop) AS "E-Tally population",

CASE WHEN exists 
(
	select 1 FROM
	postgis.vts_tally_fact tf inner join vts_campaignTargetedAreas ta 
	ON tf.campaign_id = ta.campaignId 
		AND tf.ward_code = ta.wardCode 
	WHERE tf.ward_code = ds.WardCode
)
THEN 'Yes'
ELSE 'No'
END
AS "In E-Tally Targetted Ward"
FROM public.pop_comparison pc
LEFT JOIN public.vts_dim_settlements ds ON ds.settlementObjectId = pc.settlement_settlementObjectId
LEFT JOIN public.vts_campaigns c ON c.campaignid = pc.campaign_id
--Filter where there is population
WHERE ds.statecode IN ('BA', 'BR', 'JI', 'KD', 'KN', 'KT', 'KB', 'SO', 'YO', 'ZA')

GROUP BY ds.stateName, ds.stateCode, ds.geoZone, ds.lganame, ds.lgacode, ds.lgaAmapCode, ds.wardname, ds.wardcode, ds.settlementType, ds.settlementName, ds.settlementObjectId, ds.totalFeatures, 
pc.campaign_id, c.campaignLabel,
pc.settlement_adjusted_pop,
pc.settlement_non_adjusted_pop

ORDER BY ds.statename, ds.lganame, ds.wardname, pc.campaign_id

) TO 
'D:\git\vts\src\esri\scripts\OrnlAndEtallyComparison\pop_comp.csv' WITH CSV HEADER;
--'D:\dropbox-novel-t\Dropbox (Novel-T Sarl)\Novel-T Projects\BMGF - NGA - VTS\06 - Deliverables\Analyses\eTally Population\pop_comp.csv' WITH CSV HEADER;




  	/*

  	
select ds.stateName, ds.stateCode, ds.geoZone, ds.lganame, ds.lgacode, ds.lgaAmapCode, ds.wardname, ds.wardcode, ds.settlementType, ds.settlementName, ds.totalFeatures, pc.* 
FROM public.pop_comparison pc
LEFT JOIN public.vts_dim_settlements ds ON ds.settlementObjectId = pc.settlement_settlementObjectId
ORDER BY ds.statename, ds.lganame, ds.wardname, pc.campaign_id
limit 10;

*/