select denom.objectId AS "OBJECTID", denom.globalid, pc.etally_pop,
COALESCE(SUM(fact.vaccinated), 0),
	 COALESCE(SUM(fact.household_already_vaccinated), 0),
	COALESCE(SUM(fact.household_away::integer), 0) ,
	COALESCE(SUM(fact.household_non_compliant::integer), 0),

	COALESCE(SUM(fact_raw.vaccinated), 0),
	 COALESCE(SUM(fact_raw.household_already_vaccinated), 0),
	COALESCE(SUM(fact_raw.household_away::integer), 0) ,
	COALESCE(SUM(fact_raw.household_non_compliant::integer), 0)
	
	--fact.*
from public.pop_comparison pc
left join postgis.vts_gpreflyrbuagrids denom ON pc.denom_globalid = denom.globalid
LEFT JOIN postgis.vts_tally_fact fact ON ST_Intersects(fact.shape, denom.shape)
LEFT JOIN public.etally_raw_data fact_raw ON  fact_raw.id = fact.id --ST_Intersects( ST_Transform(fact_raw.wkb_geometry, 3857), denom.shape)

where settlement_settlementObjectId = 'BUA_BA0203_84281'
and denom.globalid = '3ee27694-514d-4891-af1a-e49cba46bdc5'
and fact.revisit_type IS NULL
group by denom.objectid, pc.etally_pop
order by  denom.objectid


select 	fact.vaccinated, fact.id, fact.*
from public.pop_comparison pc
left join postgis.vts_gpreflyrbuagrids denom ON pc.denom_globalid = denom.globalid
LEFT JOIN postgis.vts_tally_fact fact ON ST_Intersects(fact.shape, denom.shape)
LEFT JOIN public.etally_raw_data fact_raw ON  fact_raw.id = fact.id --ST_Intersects( ST_Transform(fact_raw.wkb_geometry, 3857), denom.shape)

where settlement_settlementObjectId = 'BUA_BA0203_84281'
and denom.globalid = '3ee27694-514d-4891-af1a-e49cba46bdc5'
and fact.revisit_type IS NULL
order by fact.id


--vacuum analyze postgis.etally_raw_data
--vacuum analyze postgis.vts_tally_fact
--vacuum analyze postgis.vts_gpreflyrbuagrids