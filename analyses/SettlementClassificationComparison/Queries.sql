--Takes the hand drawn eTally wards from Vince and merges them into a single table.  Data imported via "D:\git\vts\src\esri\scripts\SettlementClassificationComparison\shpToPostGis.bat"
CREATE OR REPLACE FUNCTION merge_etally_wards()

RETURNS void AS
$BODY$
BEGIN

    RAISE NOTICE '%', 'Merging eTally wards to a single table';

    DROP TABLE IF EXISTS postgis.etally_wards;

    CREATE TABLE postgis.etally_wards 
    (
    id serial PRIMARY KEY,
    objectid int,
    ward_name varchar,
    lga_name varchar,
    state_name varchar,
    source varchar,
    shape geometry(Polygon,3857),
    CONSTRAINT etally_wards_unique UNIQUE (state_name, lga_name, ward_name, source)
    );


    INSERT INTO postgis.etally_wards (objectid, ward_name, lga_name, state_name, shape, source)

    SELECT objectid, ward_name, lga_name, state, ST_Transform((dump).geom, 3857) as shape, 'Jan 2016'
    from
    (
        SELECT objectid, ward_name, lga_name, state, ST_DUMP(geom) as dump
        FROM public.etallyboundaries_jan_2016
    ) sq;

    INSERT INTO postgis.etally_wards  (objectid, ward_name, lga_name, state_name, shape, source)

    SELECT objectid, ward_name, lga_name, state, ST_Transform((dump).geom, 3857) as shape, 'Dec 2015'
    from
    (
        SELECT objectid, ward_name, lga_name, state_name as state, ST_DUMP(geom) as dump
        FROM public.etally_ward_boundaries_dec_2015
    ) sq;

    INSERT INTO postgis.etally_wards  (objectid, ward_name, lga_name, state_name, shape, source)
    SELECT objectid, ward_name, lga_name, state, ST_Transform((dump).geom, 3857) as shape, 'July / Sept / Oct 2015'
    from
    (
        SELECT objectid, ward_name, lga_name, state_name as state, ST_DUMP(geom) as dump
        FROM public.etally_boundaries_jul_sep_oct
    ) sq;



    CREATE INDEX etally_wards_sidx
      ON postgis.etally_wards 
      USING gist
      (shape);

END;
$BODY$
LANGUAGE plpgsql VOLATILE;

--Takes the block fgdb and merges them to a single table
CREATE OR REPLACE FUNCTION merge_settlement_classification_blocks()

RETURNS void AS
$BODY$
DECLARE
	_state_code varchar;
	_block_table_name varchar;
BEGIN

    RAISE NOTICE '%', 'Merging blockseTally wards to a single table';

    DROP TABLE IF EXISTS postgis.settlement_classification_blocks;

    CREATE TABLE postgis.settlement_classification_blocks 
    (
        id serial PRIMARY KEY,
        objectid int NOT NULL,
        component_number int, 
        state_code varchar NOT NULL,
        landuse character varying,
        type character varying,
        shape geometry(Polygon,3857),
        CONSTRAINT settlement_classification_blocks_unique UNIQUE (objectid, state_code, component_number)
        
    );



    --JI and KD had some geometry errors that needed cleaning

    FOR i IN 1..2 LOOP

        IF i = 1 THEN 
            _state_code := 'JI';
            _block_table_name = 'jigawa';
        ELSIF i = 2 THEN 	
            _state_code := 'KD';
            _block_table_name = 'kaduna';
        END IF	;
            
        DROP VIEW IF EXISTS block_table;

        EXECUTE 'CREATE TEMPORARY VIEW block_table 
        AS SELECT * FROM public.blocks_' || _block_table_name;
            
        INSERT INTO postgis.settlement_classification_blocks  (objectid, component_number, landuse, type, shape, state_code)
        SELECT objectid, (dump).path[0], landuse, type, (dump).geom, _state_code FROM
        (
            --Transforming a valid geometry can make it invalid, so we do the transform first
            SELECT *, (ST_Dump(ST_MakeValid(ST_Transform(wkb_geometry, 3857)))) as dump
            FROM block_table
        ) sq
        where GeometryType ( (dump).geom ) NOT IN ('LINESTRING');


    END LOOP;


    INSERT INTO postgis.settlement_classification_blocks  (objectid, landuse, type, shape, state_code)
    SELECT objectid, landuse, type, (ST_Dump(ST_Transform(ST_MakeValid(wkb_geometry), 3857))).geom as shape , 'BA'
    FROM public.blocks_bauchi;

    INSERT INTO postgis.settlement_classification_blocks  (objectid, landuse, type, shape, state_code)
    SELECT objectid, landuse, type, (ST_Dump(ST_Transform(ST_MakeValid(wkb_geometry), 3857))).geom as shape , 'BO'
    FROM public.blocks_borno;

    --kano's objectid column is different
    INSERT INTO postgis.settlement_classification_blocks  (objectid, landuse, type, shape, state_code)
    SELECT objectid_12, landuse, type, (ST_Dump(ST_Transform(ST_MakeValid(wkb_geometry), 3857))).geom as shape, 'KN' 
    FROM public.blocks_kano;

    INSERT INTO postgis.settlement_classification_blocks  (objectid, landuse, type, shape, state_code)
    SELECT objectid, landuse, type, (ST_Dump(ST_Transform(ST_MakeValid(wkb_geometry), 3857))).geom as shape , 'KT'
    FROM public.blocks_katsina;

    INSERT INTO postgis.settlement_classification_blocks  (objectid, landuse, type, shape, state_code)
    SELECT objectid, landuse, type, (ST_Dump(ST_Transform(ST_MakeValid(wkb_geometry), 3857))).geom as shape, 'KB' 
    FROM public.blocks_kebbi;

    INSERT INTO postgis.settlement_classification_blocks  (objectid, landuse, type, shape, state_code)
    SELECT objectid, landuse, type, (ST_Dump(ST_Transform(ST_MakeValid(wkb_geometry), 3857))).geom as shape, 'SO' 
    FROM public.blocks_sokoto;

    INSERT INTO postgis.settlement_classification_blocks  (objectid, landuse, type, shape, state_code)
    SELECT objectid, landuse, type, (ST_Dump(ST_Transform(ST_MakeValid(wkb_geometry), 3857))).geom as shape , 'YB'
    FROM public.blocks_yobe;

    --zamfara missing landuse column
    INSERT INTO postgis.settlement_classification_blocks  (objectid, landuse, type, shape, state_code)
    SELECT objectid, NULL, type, (ST_Dump(ST_Transform(ST_MakeValid(wkb_geometry), 3857))).geom as shape , 'ZA'
    FROM public.blocks_zamfara;


    CREATE INDEX settlement_classification_blocks_sidx
      ON postgis.settlement_classification_blocks 
      USING gist
      (shape);
      
    --Remove tiny polygons (from roads / borders / etc)
    DELETE FROM postgis.settlement_classification_blocks  WHERE ST_Area(shape) < 1;

END;
$BODY$
LANGUAGE plpgsql VOLATILE;


--creates the geometry for each settlement classification block clipped by ward
CREATE OR REPLACE FUNCTION create_ward_settlement_type_table()

RETURNS void AS
$BODY$
BEGIN

    DROP TABLE IF EXISTS postgis.ward_settlement_classification_blocks CASCADE;

    CREATE TABLE postgis.ward_settlement_classification_blocks 
    (
        id serial PRIMARY KEY,
        block_objectid int,
        
        ward_objectid int,
        polygon_number int,
        
        ward_name varchar,
        lga_name varchar,
        state_name varchar,	
        type character varying,
        handmade_etally_ward boolean NOT NULL,
        ward_source varchar,
        
        under5_pop double precision,
        total_pop double precision,
        
        shape geometry(Polygon,3857),
        
        group_num int NOT NULL DEFAULT(0),
        CONSTRAINT ward_settlement_classification_blocks_unique UNIQUE (block_objectid, ward_objectid, handmade_etally_ward, polygon_number)
    );

    


    CREATE INDEX ward_settlement_classification_blocks_sidx
      ON postgis.ward_settlement_classification_blocks 
      USING gist
      (shape);

    COMMENT ON COLUMN postgis.ward_settlement_classification_blocks.ward_objectid IS 'if hand drawn, this refers to postgis.etally_wards.objectid otherwise  postgis.boundary_vaccwards.objectid';

    COMMENT ON COLUMN postgis.ward_settlement_classification_blocks.polygon_number IS 'If the intersection is a multi-polygon, this will be the number of the polygon, used mainly in the unique constraint';

    COMMENT ON COLUMN postgis.ward_settlement_classification_blocks.group_num IS 'Used to seperate by non overlapping chunks because zonal stats dont support that case';

    --First intersect the hand drawn wards
    INSERT INTO postgis.ward_settlement_classification_blocks 
    (
        ward_objectid, ward_name, lga_name, state_name, block_objectid, type, handmade_etally_ward, shape,
        polygon_number, ward_source
    )
    SELECT ward_objectid, ward_name, lga_name, state_name, block_objectid, type, true, (dump).geom, (dump).path[1], source FROM
    (
    SELECT 
        ew.objectid AS ward_objectid, ew.ward_name, ew.lga_name, ew.state_name, sc.objectid as block_objectid, sc.type,  
        ew.source,
        ST_Dump(ST_Intersection(ew.shape, sc.shape)) AS dump
    FROM postgis.settlement_classification_blocks sc
    inner join postgis.etally_wards ew
        ON ST_Intersects(ew.shape, sc.shape)
        ) sq;

    --Then targetted VTS wards 
    WITH targeted_wards AS 
    (
        select DISTINCT
        ga.stateCode,
        ga.stateName as state_name,
        ga.lgacode ,
        ga.lganame as lga_name ,
        ta.wardCode ,
        ga.wardName as ward_name from vts_campaignTargetedAreas ta
        inner join vts_campaigns c ON c.campaignid = ta.campaignid
        inner join vts_dim_geo_admin ga on ga.wardcode = ta.wardcode
        where  exists (select 1 from postgis.vts_tally_fact tf where tf.campaign_id = ta.campaignId and tf.ward_code = ga.wardCode)
    )
    INSERT INTO postgis.ward_settlement_classification_blocks 
    (
        ward_objectid,
        ward_name, 
        lga_name, 
        state_name, 
        block_objectid, 
        type, 
        handmade_etally_ward, 
        shape,
        ward_source
    )
    SELECT 
        ward_objectid, 
        ward_name,
        lga_name, 
        state_name,
        block_objectid, 
        type, 
        false,
        shape,
        'VTS'
    FROM
    (	
    SELECT 
        w.objectid as ward_objectid, 
        tw.ward_name,
        tw.lga_name, 
        tw.state_name,
        sc.objectid as block_objectid, 
        sc.type,	
        (ST_Dump(ST_Intersection(w.shape, sc.shape))).geom AS shape 
    FROM postgis.settlement_classification_blocks sc
    inner join postgis.boundary_vaccwards w
    --The not touches is to ignore cases where there is no overlap as it only returns true if the intersection is a point or line
        ON ST_Intersects(w.shape, sc.shape) AND NOT ST_Touches(w.shape, sc.shape)
    inner join targeted_wards tw ON tw.wardcode = w.wardCode
    ) sq where GeometryType(shape) NOT IN ('LINESTRING')
    ;
END;
$BODY$
LANGUAGE plpgsql VOLATILE;

--SELECT create_ward_settlement_type_table();

--Moves all overlapping polygons in given group to next one 
CREATE OR REPLACE FUNCTION check_group_number(
    _group_num int
)

RETURNS void AS
$BODY$
BEGIN

    UPDATE postgis.ward_settlement_classification_blocks AS w1
    SET group_num = _group_num+1
    WHERE EXISTS 
    (
        SELECT 1 FROM postgis.ward_settlement_classification_blocks w2
        WHERE ST_Intersects(w1.shape, w2.shape) AND NOT ST_Touches(w1.shape, w2.shape) AND w1.id > w2.id
        AND w2.group_num = w1.group_num
    ) AND group_num = _group_num;

END;
$BODY$
LANGUAGE plpgsql VOLATILE;


CREATE OR REPLACE FUNCTION create_group_number_table(
    _group_num int
)

RETURNS void AS
$BODY$
BEGIN

    EXECUTE 'DROP TABLE IF EXISTS postgis.ward_settlement_classification_blocks_' || _group_num || ' CASCADE';

    EXECUTE 'CREATE TABLE postgis.ward_settlement_classification_blocks_' || _group_num || ' AS SELECT * FROM  postgis.ward_settlement_classification_blocks 
    WHERE group_num = ' || _group_num;

END;
$BODY$
LANGUAGE plpgsql VOLATILE;


CREATE OR REPLACE FUNCTION split_ws_by_ward_into_non_overlapping(
   
)

RETURNS void AS
$BODY$
DECLARE 
    _group_num  int; 
    _db_cursor refcursor;
    _rec record;
    _sql varchar;
BEGIN

    SET log_min_messages TO 'NOTICE';

    --Drop existing tables 
    OPEN _db_cursor FOR EXECUTE
     'SELECT table_name
      FROM information_schema.tables
     WHERE table_schema=''postgis''
       AND table_type=''BASE TABLE''
       AND table_name ilike ''ward_settlement_classification_blocks\_%''';
       
    LOOP
       FETCH NEXT FROM _db_cursor INTO _rec;
       EXIT WHEN _rec IS NULL;
        
        _sql := 'DROP TABLE IF EXISTS postgis.' || _rec.table_name || ' CASCADE';
        RAISE NOTICE 'Dropping table with %', _sql;
        
        EXECUTE _sql;
        
    END LOOP;
    
    
    

    --Reset group numbers 
    UPDATE postgis.ward_settlement_classification_blocks
    SET group_num = 0;
    
    --Create a view containing overlapping polygons
    DROP VIEW IF EXISTS postgis.ward_settlement_classification_blocks_overlapping;
    
    CREATE VIEW postgis.ward_settlement_classification_blocks_overlapping AS select * from postgis.ward_settlement_classification_blocks w1
    WHERE EXISTS 
    (
        SELECT 1 FROM postgis.ward_settlement_classification_blocks w2
        WHERE ST_Intersects(w1.shape, w2.shape) AND NOT ST_Touches(w1.shape, w2.shape) AND w1.id != w2.id
        AND w2.group_num = w1.group_num
    );

    _group_num = 0 ;
    --PERFORM    create_group_number_table(0);
        
    WHILE EXISTS (SELECT 1 FROM postgis.ward_settlement_classification_blocks_overlapping) LOOP 
        RAISE NOTICE 'Creating group %', _group_num;
        
        PERFORM check_group_number(_group_num);
        PERFORM create_group_number_table(_group_num);
        
        _group_num := _group_num + 1; 
    END LOOP;
    
    --Export remaining group 
    PERFORM create_group_number_table(_group_num);


END;
$BODY$
LANGUAGE plpgsql VOLATILE;

CREATE OR REPLACE FUNCTION clean_zonal_stats_tables
(
    
)
RETURNS VOID AS
$BODY$
DECLARE
    _db_cursor refcursor;
    _rec record;
    _sql varchar;
BEGIN 
    --Drop zonal stat tables 
    OPEN _db_cursor FOR EXECUTE
     'SELECT table_name, table_schema
      FROM information_schema.tables
     WHERE table_type=''BASE TABLE''
       AND (table_name ilike ''zonalstats_under5%'' OR table_name ilike ''zonalstats_total%'')';
       
    LOOP
       FETCH NEXT FROM _db_cursor INTO _rec;
       EXIT WHEN _rec IS NULL;
        
        _sql := 'DROP TABLE IF EXISTS ' || _rec.table_schema || '.' || _rec.table_name || ' CASCADE';
        RAISE NOTICE 'Dropping table with %', _sql;
        
        EXECUTE _sql;
        
    END LOOP;
    
END;
$BODY$
LANGUAGE plpgsql VOLATILE;


CREATE OR REPLACE FUNCTION merge_zonal_stats_tables
(
    _name_part varchar
)
RETURNS VOID AS
$BODY$
DECLARE
    _sql varchar;    
    _db_cursor refcursor;
    _rec record;
BEGIN 

    
    _sql := 'DROP TABLE IF EXISTS postgis.zonalstats_' || _name_part || '_9by9';
    EXECUTE(_sql);
    
    _sql := 'CREATE TABLE postgis.zonalstats_' || _name_part || '_9by9
    (
      objectid integer,
      wscb_id integer,
      count integer,
      area double precision,
      sum double precision,
      UNIQUE (wscb_id)
    )';
    
    EXECUTE(_sql);

    OPEN _db_cursor FOR EXECUTE
     'SELECT table_name
      FROM information_schema.tables
     WHERE table_schema=''postgis''
       AND table_type=''BASE TABLE''
       AND table_name ilike ''ZONALSTATS_' || _name_part || '_9by9\_%''';
       
    LOOP
       FETCH NEXT FROM _db_cursor INTO _rec;
       EXIT WHEN _rec IS NULL;

        
       
        _sql := 'INSERT INTO postgis.ZONALSTATS_' || _name_part || '_9by9       
        SELECT * FROM postgis.' || _rec.table_name;
        
        
        RAISE NOTICE 'Insert merged %', _sql;
        EXECUTE _sql;
       --PRINT _sql 
       --#logMessageNoQuotes("_sql") 
       
       
       
       
       RAISE NOTICE 'rec: %', _rec; 
    END LOOP;
END;
$BODY$
LANGUAGE plpgsql VOLATILE;


--Table to store eTally points in each ward_settlement_classification_blocks entry
CREATE OR REPLACE FUNCTION create_etally_pop_per_sc()

RETURNS void AS
$BODY$
BEGIN

    DROP TABLE IF EXISTS postgis.ward_settlement_classification_blocks_etally;

    CREATE TABLE postgis.ward_settlement_classification_blocks_etally
    (
      id serial PRIMARY KEY,
      ward_settlement_classification_blocks_id integer REFERENCES postgis.ward_settlement_classification_blocks(id),
      vts_tally_fact_id integer REFERENCES postgis.vts_tally_fact(id),
      campaign_id integer REFERENCES public.vts_campaigns(campaignId) NOT NULL,
      inside_eligible int,
      outside_eligible int,
      CONSTRAINT ward_settlement_classification_blocks_etally_unique UNIQUE (ward_settlement_classification_blocks_id, vts_tally_fact_id)
    );

    INSERT INTO postgis.ward_settlement_classification_blocks_etally
    (
        ward_settlement_classification_blocks_id, 
        vts_tally_fact_id, 
        campaign_id,
        inside_eligible, 
        outside_eligible
    )
    SELECT 
        wsc.id, 
        tf.id,
        tf.campaign_id,
        CASE WHEN COALESCE(tf.outside_vaccinated, 0) <= 0 THEN tf.household_eligible ELSE 0 END AS  inside_eligible,
        COALESCE(tf.outside_vaccinated, 0) AS outside_eligible
    FROM 
        postgis.ward_settlement_classification_blocks wsc 
        INNER JOIN postgis.vts_tally_fact tf ON ST_Intersects(tf.shape, wsc.shape)
    WHERE tf.revisit_type IS NULL;

END;
$BODY$
LANGUAGE plpgsql VOLATILE;

--Sums up the GIS population per ward settlement classification block
CREATE OR REPLACE FUNCTION update_pop_in_ward_settlement_classification_blocks()

RETURNS void AS
$BODY$
BEGIN
                   
    UPDATE postgis.ward_settlement_classification_blocks AS wsc 
    SET under5_pop = (select 
    --Here we divide by 100 for the same reason, also since the raster was converted to int by multiplying by 1e6, here we divide to get the original value back
            SUM(zu9.sum / (100 * 1000000)) as "Under 5 Population"
            FROM postgis.zonalstats_under5_9by9 zu9 WHERE zu9.wscb_id = wsc.id
            ),
            --it's divided by 100 because it contains the unaltered values of the 90m x 90m pop raster
            --so in the 9m x 9m raster, each square will have 1/100 of the pop.
        total_pop = 
            (SELECT SUM(zt9.sum / 100) as "Total GIS Population"
            FROM postgis.zonalstats_total_9by9 zt9 WHERE zt9.wscb_id = wsc.id);
            

    DROP TABLE IF EXISTS postgis.ward_settlement_classification_blocks_etally_pop;
    
    --Store the eTally pop per campaign as some wards can be covered in multiple campaigns
    CREATE TABLE postgis.ward_settlement_classification_blocks_etally_pop
    (
        id serial PRIMARY KEY,
        campaign_id int,
        campaign_label varchar,
        campaign_start_date date,
        inside_eligible int,
        total_eligible int,
        ward_settlement_classification_blocks_id int REFERENCES postgis.ward_settlement_classification_blocks(id) ON DELETE CASCADE
    );
    
    INSERT INTO postgis.ward_settlement_classification_blocks_etally_pop
    (
        campaign_id,
        campaign_label,
        campaign_start_date,
        inside_eligible,
        total_eligible,
        ward_settlement_classification_blocks_id
    )
    SELECT  
        campaign_id,
        c.CampaignLabel,
        c.StartDate,
        
        SUM(wsc_e.inside_eligible) AS Inside_Eligible,        
        COALESCE(SUM(wsc_e.outside_eligible),0) + COALESCE(SUM(wsc_e.inside_eligible),0) AS Total_Eligible,
        wsc.id        
    FROM 
    postgis.ward_settlement_classification_blocks AS wsc 
    INNER JOIN postgis.ward_settlement_classification_blocks_etally wsc_e 
        ON wsc.id = wsc_e.ward_settlement_classification_blocks_id
    INNER JOIN public.vts_campaigns c ON c.campaignid = wsc_e.campaign_id 
    GROUP BY wsc.id, campaign_id, c.CampaignLabel, c.startDate;
            
END;
$BODY$
LANGUAGE plpgsql VOLATILE;

CREATE OR REPLACE FUNCTION export_csv()


RETURNS void AS
$BODY$
BEGIN

COPY (
    SELECT 
        wsc.id,
        ep.campaign_id AS "Campaign Id",
        ep.campaign_label AS "Campaign Label",
        ep.campaign_start_date AS "Campaign Start Date",
        wsc.state_name AS "State", ga.stateCode AS "State Code", 
        wsc.lga_name AS "LGA", ga.lgaCode AS "LGA Code", 
        wsc.ward_name AS "Ward", ga.wardCode AS "Ward Code",
        wsc.ward_source AS "Ward Source",
        wsc.type AS "Settlement Classification",
        CASE WHEN wsc.handmade_etally_ward THEN 'Yes' ELSE 'No' END AS "Is Custom eTally Ward?",
        ep.inside_eligible AS "Inside Elgible",
        ep.total_eligible - ep.inside_eligible AS "Outside Elgible",
        ep.total_eligible AS "Total Elgible",
        
        wsc.total_pop AS "Total GIS Population",
        
        wsc.under5_pop AS "<5 GIS Population"
    FROM 
        postgis.ward_settlement_classification_blocks wsc 
        LEFT JOIN vts_dim_geo_admin ga ON ga.wardName = wsc.ward_name AND ga.lgaName = wsc.lga_name AND ga.stateName = wsc.state_name 
        LEFT JOIN postgis.ward_settlement_classification_blocks_etally_pop ep ON ep.ward_settlement_classification_blocks_id = wsc.id 
    WHERE 
        ( 
            (wsc.ward_source = 'Dec 2015' AND ep.campaign_label = 'Dec 2015 IPD') 
            OR 
            (wsc.ward_source = 'Jan 2016' AND ep.campaign_label = 'Jan 2016 IPD') 
            OR 
            ( wsc.ward_source NOT IN ('Dec 2015', 'Jan 2016') )
        )
        AND 
        (
            COALESCE(ep.total_eligible, 0) > 0 
            OR 
            COALESCE(wsc.total_pop,0) > 0
        )
) TO 'D:\git\vts\src\esri\scripts\SettlementClassificationComparison\sc_block_pop.csv' WITH CSV HEADER;

--=IF('Inside Elgible' > 0, '<5 GIS Population' / 'Inside Elgible' ,  0)
--=IF('Total Elgible' > 0, '<5 GIS Population' / 'Total Elgible' ,  0)

END;
$BODY$
LANGUAGE plpgsql VOLATILE;


CREATE OR REPLACE FUNCTION create_single_settlement_table()

RETURNS void AS
$BODY$
BEGIN

    DROP TABLE IF EXISTS postgis.vts_settlements;
    
    CREATE TABLE postgis.vts_settlements
    (
        id serial PRIMARY KEY,
        global_id uuid NOT NULL,
        ward_code varchar NOT NULL,
        settlement_type varchar NOT NULL,
        shape geometry(MultiPolygon,3857) NOT NULL,
        area double precision,
        
        CONSTRAINT vts_settlements_unique UNIQUE(global_id)
    );

    INSERT INTO postgis.vts_settlements (global_id, ward_code, settlement_type, shape)
    SELECT 
        globalid,
        wardcode,
        'BUA',
        shape 
    FROM 
        postgis.fe_BuiltUpArea;
    
    INSERT INTO postgis.vts_settlements (global_id, ward_code, settlement_type, shape)
    SELECT 
        globalid,
        wardcode,
        'HA',
        shape 
    FROM 
        postgis.fe_hamletareas;
        
    INSERT INTO postgis.vts_settlements (global_id, ward_code, settlement_type, shape)
    SELECT 
        globalid,
        wardcode,
        'SSA',
        ST_Multi(shape)
    FROM 
        postgis.fe_smlsettlementareas;
        
    UPDATE postgis.vts_settlements
    SET area = ST_Area(shape);
    
    
    CREATE INDEX vts_settlements_sidx
      ON postgis.vts_settlements
      USING gist
      (shape);
END;
$BODY$
LANGUAGE plpgsql VOLATILE;

CREATE OR REPLACE FUNCTION classify_settlements()

RETURNS void AS
$BODY$
DECLARE

BEGIN
    DROP TABLE IF EXISTS postgis.vts_settlements_classification;
    
    CREATE TABLE postgis.vts_settlements_classification
    (
        id serial PRIMARY KEY,
        vts_settlements_id integer NOT NULL REFERENCES postgis.vts_settlements,
        settlement_classification_blocks_id integer NOT NULL REFERENCES postgis.settlement_classification_blocks,
        
        polygon_number int, 
        
        type varchar NOT NULL ,
        
        shape geometry(Polygon,3857) NOT NULL,        
        area double precision NOT NULL,
        area_percentage double precision NOT NULL,
        
        --There  can be multiple polygons intersections between a block and a settlement
        CONSTRAINT vts_settlements_classification_unique UNIQUE(vts_settlements_id, settlement_classification_blocks_id, polygon_number )
    );

    INSERT INTO postgis.vts_settlements_classification
    (
        vts_settlements_id,
        settlement_classification_blocks_id,
        type,
        shape,
        area,
        area_percentage,
        polygon_number
    )
    SELECT vs_id, cb_id, type, (dump).geom, ST_Area( (dump).geom ), ST_Area( (dump).geom ) / area, (dump).path[1] FROM
    (
        select cb.id AS cb_id, vs.id AS vs_id, ST_Dump(ST_Intersection(cb.shape, vs.shape)) AS Dump, cb.type, vs.area 
        FROM postgis.settlement_classification_blocks cb
            INNER JOIN postgis.vts_settlements vs ON 
                ST_Intersects(vs.shape, cb.shape) 
            
    ) sq WHERE GeometryType( (dump).geom ) NOT IN ('POINT');


END;
$BODY$
LANGUAGE plpgsql VOLATILE;

CREATE OR REPLACE FUNCTION export_vts_settlement_classification_csv()


RETURNS void AS
$BODY$
BEGIN

    
CREATE EXTENSION IF NOT EXISTS tablefunc;

    COPY 
    (
        SELECT
        ga.stateName AS "State", ga.stateCode AS "State Code", 
        ga.lgaName AS "LGA", ga.lgaCode AS "LGA Code", 
        ga.wardName AS "Ward", ga.wardCode AS "Ward Code",
        sq.*, 
        "A" / "Settlement Area" AS "A%",
        "B" / "Settlement Area" AS "B%",
        "C" / "Settlement Area" AS "C%",
        "D" / "Settlement Area" AS "D%",
        "E" / "Settlement Area" AS "E%",
        "F" / "Settlement Area" AS "F%" ,
        "M" / "Settlement Area" AS "M%", 
        "Z" / "Settlement Area" AS "Z%" ,

        "Unclassified" / "Settlement Area" AS "Unclassified %" 

        FROM
        (
            SELECT  
            COALESCE("A",0) +
            COALESCE("B",0) +
            COALESCE("C",0) +
            COALESCE("D",0) +
            COALESCE("E",0) +
            COALESCE("F",0) +
            COALESCE("M",0) +
            COALESCE("Z",0)

            AS "Classified Area", "Settlement Area" - ( 
            COALESCE("A",0) +
            COALESCE("B",0) +
            COALESCE("C",0) +
            COALESCE("D",0) +
            COALESCE("E",0) +
            COALESCE("F",0) +
            COALESCE("M",0) +
            COALESCE("Z",0)) AS "Unclassified", * FROM
            crosstab(
            $$
            WITH targeted_wards AS 
                (
                    select DISTINCT        
                    ta.wardCode AS ward_code
                    from vts_campaignTargetedAreas ta
                    inner join vts_campaigns c ON c.campaignid = ta.campaignid
                    inner join vts_dim_geo_admin ga on ga.wardcode = ta.wardcode
                    where  exists (select 1 from postgis.vts_tally_fact tf where tf.campaign_id = ta.campaignId and tf.ward_code = ga.wardCode)
                )
            select vs.id, vs.ward_code, vs.settlement_type, vs.area AS "Settlement Area", sc.type, SUM(sc.area) AS area 
            --SUM(sc.area_percentage) AS percentage 
            from postgis.vts_settlements vs
            LEFT JOIN postgis.vts_settlements_classification sc ON vs.id = sc.vts_settlements_id
            INNER JOIN targeted_wards tw on tw.ward_code = vs.ward_code
            group by vs.id, vs.ward_code, vs.settlement_type, vs.area, sc.type
            order by vs.id
            $$,
            $$VALUES ('A'), ('B'), ('C'), ('D'), ('E'), ('F'), ('M'), ('Z')
            $$)
            AS crosstable("Id" integer, "Ward Code" varchar, "Set type" varchar, "Settlement Area" double precision,
             "A" double precision, "B" double precision, "C" double precision, 
             "D" double precision, 
             "E" double precision, 
             "F" double precision, 
             "M" double precision, "Z" double precision)
        ) sq
        LEFT JOIN vts_dim_geo_admin ga ON sq."Ward Code" = ga.wardCode
       
        WHERE COALESCE("A",0) +
        COALESCE("B",0) +
        COALESCE("C",0) +
        COALESCE("D",0) +
        COALESCE("E",0) +
        COALESCE("F",0) +
        COALESCE("M",0) +
        COALESCE("Z",0) > 0
    ) TO 'D:\git\vts\src\esri\scripts\SettlementClassificationComparison\vts_settlement_classifications.csv' WITH CSV HEADER;
    
    

END;
$BODY$
LANGUAGE plpgsql VOLATILE;
----------------------------------------
--Handle "hand made" wards 
----------------------------------------

--select merge_etally_wards();


----------------------------------------
--Merge the settlement blocks to a single table
----------------------------------------

--SELECT merge_settlement_classification_blocks();

----------------------------------------
--Slice the settlement blocks by ward
----------------------------------------

--SELECT create_ward_settlement_type_table();

----------------------------------------
--Split the settlement blocks by ward into non overlapping groups
----------------------------------------

--SELECT split_ws_by_ward_into_non_overlapping();



----------------------------------------
--Export ward settlement blocks to FGDB
--D:\git\vts\src\esri\scripts\SettlementClassificationComparison\wardSCToEsri.bat

--Run zonal stats 

--Clean FGDB
--Reimport results using ZonalStatsToPostgis.bat

----------------------------------------

----------------------------------------
--Merge the imported zonal stat tables from ZonalStatsToPostgis.bat 
----------------------------------------

--SELECT merge_zonal_stats_tables('under5');

--SELECT merge_zonal_stats_tables('total');




----------------------------------------
--Sum the eTally population
----------------------------------------
--SELECT create_etally_pop_per_sc();

----------------------------------------
--Update GIS pop per ward settlement block
----------------------------------------
--SELECT update_pop_in_ward_settlement_classification_blocks();


----------------------------------------
--Export to CSV 
----------------------------------------
--SELECT export_csv();

SET log_min_messages TO 'NOTICE';