/*select campaign_id, sum(etally_pop) from public.pop_comparison
where settlement_settlementObjectId = 'BUA_KN1203_13188'
group by campaign_id
LIMIT 10;
*/
/*
select * from public.vts_dim_settlements ds
where settlementName = 'Fagge C'
limit 10
*/

select sum(etally_pop) as pop, sum(new_method), sum(outside) as no_outside, sum(household_eligible) as household_eligible from
(
select denom.objectId AS "OBJECTID", denom.globalid, pc.etally_pop,

COALESCE(SUM(fact.vaccinated), 0) +
	 --COALESCE(SUM(fact.household_already_vaccinated), 0) +
	COALESCE(SUM(fact.household_away::integer), 0) +
	COALESCE(SUM(fact.household_non_compliant::integer), 0) as new_method,

COALESCE(SUM(fact.vaccinated), 0) +
	COALESCE(SUM(fact.household_already_vaccinated), 0) +
	COALESCE(SUM(fact.household_away::integer), 0) +
	COALESCE(SUM(fact.household_non_compliant::integer), 0) -
	COALESCE(SUM(fact.outside_vaccinated::integer), 0) as outside,

	COALESCE(SUM(fact.vaccinated), 0) as vacc,
	COALESCE(SUM(fact.household_already_vaccinated), 0) as already,
	COALESCE(SUM(fact.household_away::integer), 0) as away,
	COALESCE(SUM(fact.household_non_compliant::integer), 0) as non_c,
	COALESCE(SUM(fact.outside_vaccinated::integer), 0) as outside_vac,

	sum(fact.household_eligible) as household_eligible
/*
	COALESCE(SUM(fact_raw.vaccinated), 0),
	 COALESCE(SUM(fact_raw.household_already_vaccinated), 0),
	COALESCE(SUM(fact_raw.household_away::integer), 0) ,
	COALESCE(SUM(fact_raw.household_non_compliant::integer), 0)
*/	
	--fact.*
from public.pop_comparison pc
left join postgis.vts_gpreflyrbuagrids denom ON pc.denom_globalid = denom.globalid
LEFT JOIN postgis.vts_tally_fact fact ON ST_Intersects(fact.shape, denom.shape)
--LEFT JOIN public.etally_raw_data fact_raw ON  fact_raw.id = fact.id --ST_Intersects( ST_Transform(fact_raw.wkb_geometry, 3857), denom.shape)

where settlement_settlementObjectId = 'BUA_BA0203_84281'
--and denom.globalid = '3ee27694-514d-4891-af1a-e49cba46bdc5'
and fact.revisit_type IS NULL
--and COALESCE(fact.outside_vaccinated, 0) <= 0
group by denom.objectid, pc.etally_pop
--order by  denom.objectid
) sq
--drop table public.pop_comparison

/*

select 	fact.vaccinated, fact.id, fact.*
from public.pop_comparison pc
left join postgis.vts_gpreflyrbuagrids denom ON pc.denom_globalid = denom.globalid
LEFT JOIN postgis.vts_tally_fact fact ON ST_Intersects(fact.shape, denom.shape)
LEFT JOIN public.etally_raw_data fact_raw ON  fact_raw.id = fact.id --ST_Intersects( ST_Transform(fact_raw.wkb_geometry, 3857), denom.shape)

where settlement_settlementObjectId = 'BUA_BA0203_84281'
and denom.globalid = '3ee27694-514d-4891-af1a-e49cba46bdc5'
and fact.revisit_type IS NULL
order by fact.id

*/
--vacuum analyze postgis.etally_raw_data
--vacuum analyze postgis.vts_tally_fact
--vacuum analyze postgis.vts_gpreflyrbuagrids