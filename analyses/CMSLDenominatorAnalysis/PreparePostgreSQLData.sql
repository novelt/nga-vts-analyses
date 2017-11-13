DROP SCHEMA IF EXISTS temp CASCADE ;

CREATE SCHEMA temp;

CREATE OR REPLACE FUNCTION temp.create_temp_vts_fact_settlement_feature_history
(
)
RETURNS void AS
$BODY$
DECLARE
BEGIN
    
    DROP TABLE IF EXISTS temp.vts_fact_settlement_feature_history;
    
    CREATE TABLE temp.vts_fact_settlement_feature_history
    (
      id bigint PRIMARY KEY,
      campaignid smallint,
      campaignstartdate timestamp without time zone,
      settlementobjectid character varying(255),
      gpreflyrobjectid integer,
      isvisited boolean,
      iscovered boolean,
      isnewlycovered boolean,
      waspreviouslycovered boolean,
      waspreviouslycoverednbroundago smallint,
      waspreviouslycoveredcampaignid smallint,
      nboftimestrackedasatround smallint,
      nboftimestrackedtotal smallint,
      num_times_prev_missed_consecutive bigint,
      num_times_prev_missed bigint
    );

    INSERT INTO temp.vts_fact_settlement_feature_history
    SELECT *, 0,0 FROM public.vts_fact_settlement_feature_history;
    
    INSERT INTO temp.vts_fact_settlement_feature_history
    (id, num_times_prev_missed_consecutive, num_times_prev_missed)
    SELECT   id, 
        --case when isVisited = false AND  lag(isVisited, 1) OVER w = false then 1 else 0 end  AS is_repeat_missed
            count(*) over w AS num_times_prev_missed_consecutive,
            count(*) over w2 AS num_times_prev_missed
        FROM vts_fact_settlement_feature_history
        WHERE         
            isVisited = false
        WINDOW 
            w as (Partition by settlementobjectid, gpRefLyrObjectId, wasPreviouslyCoveredCampaignId ORDER BY campaignStartDate),
            w2 as (Partition by settlementobjectid, gpRefLyrObjectId ORDER BY campaignStartDate)
        ORDER BY settlementObjectId, gpRefLyrObjectId, campaignStartDate
    ON CONFLICT(id) DO UPDATE 
        SET num_times_prev_missed_consecutive = EXCLUDED.num_times_prev_missed_consecutive, 
            num_times_prev_missed = EXCLUDED.num_times_prev_missed;
        
        /*
    UPDATE temp.vts_fact_settlement_feature_history
    SET 
        num_times_prev_missed_consecutive = sq.num_times_prev_missed_consecutive, num_times_prev_missed = sq.num_times_prev_missed
    FROM 
    (
        SELECT   id, 
            --case when isVisited = false AND  lag(isVisited, 1) OVER w = false then 1 else 0 end  AS is_repeat_missed
                count(*) over w AS num_times_prev_missed_consecutive,
                count(*) over w2 AS num_times_prev_missed
            FROM vts_fact_settlement_feature_history
            WHERE         
                isVisited = false
            WINDOW 
                w as (Partition by settlementobjectid, gpRefLyrObjectId, wasPreviouslyCoveredCampaignId ORDER BY campaignStartDate),
                w2 as (Partition by settlementobjectid, gpRefLyrObjectId ORDER BY campaignStartDate)
            ORDER BY settlementObjectId, gpRefLyrObjectId, campaignStartDate
    ) sq 
    WHERE sq.id = h.id;
    */
    
    --Calculate num_times_prev_missed for non visited
    INSERT INTO temp.vts_fact_settlement_feature_history as h
    (id, num_times_prev_missed)
    SELECT id, count(*) over w2 as num_times_prev_missed 
        FROM temp.vts_fact_settlement_feature_history 
        WHERE isVisited = false
        WINDOW w2 as 
        (
            PARTITION BY settlementobjectid, gpRefLyrObjectId ORDER BY campaignStartDate
        )
    
    ON CONFLICT(id) DO UPDATE 
        SET num_times_prev_missed = EXCLUDED.num_times_prev_missed;
    

    --Calculate num_times_prev_missed for Visited
    INSERT INTO temp.vts_fact_settlement_feature_history as h
    (id, num_times_prev_missed)
    SELECT id, nbOfTimesTrackedAsAtRound - count(*) over w2 as num_times_prev_missed 
        FROM temp.vts_fact_settlement_feature_history 
        WHERE isVisited = true
        WINDOW w2 as 
        (
            PARTITION BY settlementobjectid, gpRefLyrObjectId ORDER BY campaignStartDate
        )
    
    ON CONFLICT(id) DO UPDATE 
        SET num_times_prev_missed = EXCLUDED.num_times_prev_missed;
    

        
END;
$BODY$
LANGUAGE plpgsql VOLATILE;  

/*
Creates a table temp.<_field_name> containing a pivot table with each campaign as columns
*/
CREATE OR REPLACE FUNCTION temp.cross_tab_denom
(
    _field_name varchar,
    _field_type varchar
)
RETURNS void AS
$BODY$
DECLARE
    _sql varchar = '';
    _value_list varchar = '';
    _columns_list varchar = '';
BEGIN
    SELECT 'VALUES ' || string_agg( '(''' || _field_name || '_' || startdate::date || ''')', ', ')
    INTO _value_list
    FROM 
    ( 
        select startdate 
        from vts_campaigns   
        ORDER BY startdate
    ) sq;
 
    SELECT  string_agg( '"' || _field_name || '_' || startdate::date || '" ' || _field_type, ', ')
    INTO _columns_list
    FROM 
    ( 
        select startdate 
        from vts_campaigns   
        ORDER BY startdate
    ) sq;

--h.gpRefLyrObjectId = 571880    
   --WHERE settlementObjectId = ''BUA_40101_13413''
    _sql = 'SELECT * FROM crosstab(
$$
SELECT h.gpRefLyrObjectId, h.settLementObjectId, ''' || _field_name || '_'' ||
    campaignStartDate::date, h.' || _field_name || ' 
FROM temp.vts_fact_settlement_feature_history h 

ORDER BY settLementObjectId, gpRefLyrObjectId
$$,
$$ ' || _value_list || '
$$
)
AS nb_of_times_tracked_as_at_round
(
	denom_objectid int,
	settlement_object_id varchar,
    ' || _columns_list || '
)';

    EXECUTE 'DROP TABLE IF EXISTS temp.' || _field_name || ' CASCADE';
    
    EXECUTE 'CREATE TABLE temp.' || _field_name || '  AS (' || _sql || ')   ';

    RAISE NOTICE '%', _sql;
END;
$BODY$
LANGUAGE plpgsql VOLATILE;  

SELECT temp.create_temp_vts_fact_settlement_feature_history();

/*
SELECT temp.cross_tab_denom('nbOfTimesTrackedAsAtRound', 'int' );
SELECT temp.cross_tab_denom('isVisited', 'boolean' );
SELECT temp.cross_tab_denom('num_times_prev_missed_consecutive', 'int' );
SELECT temp.cross_tab_denom('num_times_prev_missed', 'int' );

DO 
$do$ 
DECLARE
    _sql varchar = '';
    _joins varchar;
    _field_name varchar;
    _fields varchar;
BEGIN 
    
    SELECT string_agg( 'temp.' || field_name || '."' || field_name || '_' || startdate || '"', ', ')
    INTO STRICT _fields
    FROM 
    (
        SELECT field_name, startdate::date  
            FROM (VALUES 
                ('isVisited', 1), 
                ('nbOfTimesTrackedAsAtRound', 2),
                ('num_times_prev_missed_consecutive', 3),
                ('num_times_prev_missed', 4)
            ) AS t(field_name, o),
        vts_campaigns
        ORDER BY startdate, o    
    ) sq;
    
    SELECT string_agg( 'INNER JOIN temp.' || field_name || ' ON temp.' || field_name || '.denom_objectid = temp.isVisited.denom_objectid AND temp.' || field_name || '.settlement_object_id = temp.isVisited.settlement_object_id', ' ')
    INTO STRICT _joins
    FROM (VALUES 
        ('nbOfTimesTrackedAsAtRound', 2),
        ('num_times_prev_missed_consecutive', 3),
        ('num_times_prev_missed', 4)
    ) AS t(field_name, o);

    DROP TABLE IF EXISTS temp.t_all;
    
    _sql := 
    'CREATE TABLE temp.t_all AS 
        SELECT NULL::Geometry(MultiPolygon, 3857) AS shape, temp.isVisited.settlement_object_id,  temp.isVisited.denom_objectid, ' || _fields || '
        FROM temp.isVisited ' || _joins;
            
    RAISE NOTICE '%', _sql;
    
    EXECUTE _sql;
   
    
    UPDATE temp.t_all AS t
    SET shape = ST_Multi(f.shape)
    FROM postgis.vts_gpreflyrbuagrids f
    WHERE f.settlementObjectid = t.settlement_object_id 
        AND f.objectid = t.denom_objectid;

    UPDATE temp.t_all AS t
    SET shape = ST_Multi(f.shape)
    FROM postgis.vts_gpreflyrhabuffers f
    WHERE f.settlementObjectid = t.settlement_object_id 
        AND f.objectid = t.denom_objectid;

    UPDATE temp.t_all AS t
    SET shape = ST_Multi(f.shape)
    FROM postgis.vts_gpreflyrbuagrids f
    WHERE f.settlementObjectid = t.settlement_object_id 
        AND f.objectid = t.denom_objectid;

END
$do$;
*/

/*
DO 
$do$ 
    DECLARE _sql varchar;
BEGIN 
    SELECT cross_tab_denom('nbOfTimesTrackedAsAtRound',  'vts_gpRefLyrBuaGrids', 'bua' )
    INTO _sql;
    
    EXECUTE _sql || '  ';
    
    --EXECUTE 'COPY (' || _sql || ') TO ''D:\git\nga-gis-vts-gdb\Debug and Utility Scripts\AutoCRossTab.csv'' WITH CSV HEADER';
    EXECUTE 'CREATE TEMPORARY TABLE t1 ON COMMIT PRESERVE ROWS AS (' || _sql || ')   ';

END
$do$;

COPY (select * from t1) TO STDOUT;
*/