import time
import json

from ..config import settings
from ..models.score_model import ScoreAgg, Weights
from asyncpg.pool import Pool
from loguru import logger

async def fetch_rows(
        *args,
        sql_query: str,
        pool: Pool
):
    start_time = time.perf_counter()
    logger.debug(f"Execute query: {sql_query}")
    # Take a connection from the pool.
    async with pool.acquire() as connection:
        # Open a transaction.
        async with connection.transaction():
            with connection.query_logger(logger.trace):
                # Run the query passing the request argument.
                try:
                    rows = await connection.fetch(
                        sql_query,
                        *args,
                        timeout=settings.POSTGRES_TIMEOUT_SECS
                    )
                except Exception as e:
                    logger.error(f"Failed to execute query: {sql_query}")
                    logger.error(f"{e}")
                    return [{"Unknown error. Contact K3L team"}]
    logger.info(f"db took {time.perf_counter() - start_time} secs for {len(rows)} rows")
    return rows

async def get_unique_fid_metadata_for_handles(
        handles: list[str],
        pool: Pool,
):
    sql_query = """
    SELECT
        '0x' || encode(any_value(fids.custody_address), 'hex') as address,
        any_value(fnames.fname) as fname,
        any_value(user_data.value) as username,
        fids.fid as fid
    FROM fids
    INNER JOIN fnames ON (fids.fid = fnames.fid)
    LEFT JOIN user_data ON (user_data.fid = fids.fid and user_data.type=6)
    WHERE
        (fnames.fname = ANY($1::text[]))
        OR
        (user_data.value = ANY($1::text[]))
    GROUP BY fids.fid
    LIMIT 1000 -- safety valve
    """
    return await fetch_rows(handles, sql_query=sql_query, pool=pool)

async def get_top_profiles(strategy_id: int, offset: int, limit: int, pool: Pool):
    sql_query = """
    WITH total AS (
        SELECT count(*) as total from k3l_rank WHERE strategy_id = $1
    )
    SELECT
        profile_id as fid,
        rank,
        score,
        ((total.total - (rank - 1))*100 / total.total) as percentile
    FROM k3l_rank
    CROSS JOIN total
    WHERE strategy_id = $1
    ORDER BY rank
    OFFSET $2
    LIMIT $3
    """
    return await fetch_rows(strategy_id, offset, limit, sql_query=sql_query, pool=pool)

async def get_top_channel_profiles(
        channel_id: str,
        offset: int,
        limit: int,
        lite: bool,
        pool: Pool
):
    if lite:
        sql_query = """
        SELECT
            ch.fid,
            rank
        FROM k3l_channel_fids as ch
        WHERE 
            channel_id = $1 
            AND 
            compute_ts=(select max(compute_ts) from k3l_channel_fids where channel_id=$1)
        ORDER BY rank ASC
        OFFSET $2
        LIMIT $3
        """
    else:
        sql_query = """
        WITH total AS (
            SELECT count(*) as total from k3l_channel_fids 
            WHERE channel_id = $1
            AND compute_ts=(select max(compute_ts) from k3l_channel_fids where channel_id=$1)
        ),
        addresses as (
        SELECT '0x' || encode(fids.custody_address, 'hex') as address, fid
        FROM fids
        UNION ALL 
         SELECT v.claim->>'address' as address, fid
         FROM verifications v 
        ),
        top_records as (
        SELECT
            ch.fid,
            rank,
            score,
            ((total.total - (rank - 1))*100 / total.total) as percentile
        FROM k3l_channel_fids as ch
        CROSS JOIN total
        WHERE 
            channel_id = $1 
            AND 
            compute_ts=(select max(compute_ts) from k3l_channel_fids where channel_id=$1)
        ORDER BY rank ASC
        OFFSET $2
        LIMIT $3
        ),
        mapped_records as (
        SELECT top_records.*,addresses.address 
        FROM top_records 
        LEFT JOIN addresses using (fid)
        )
        select fid,
        any_value(rank) as rank,
        any_value(score) as score,
        ARRAY_AGG(DISTINCT address) as addresses
        FROM mapped_records
        GROUP BY fid
        ORDER by rank
        """
    return await fetch_rows(channel_id, offset, limit, sql_query=sql_query, pool=pool)

async def get_profile_ranks(strategy_id: int, fids: list[int], pool: Pool):
    sql_query = """
    WITH total AS (
        SELECT count(*) as total from k3l_rank WHERE strategy_id = $1
    )
    SELECT
        profile_id as fid,
        rank,
        score,
        ((total.total - (rank - 1))*100 / total.total) as percentile
    FROM k3l_rank
    CROSS JOIN total
    WHERE
        strategy_id = $1
        AND profile_id = ANY($2::integer[])
    ORDER BY rank
    """
    return await fetch_rows(strategy_id, fids, sql_query=sql_query, pool=pool)

async def get_channel_profile_ranks(
        channel_id: str,
        fids: list[int],
        lite: bool,
        pool: Pool
):
    if lite:
        sql_query = """
        SELECT
            ch.fid,
            rank
        FROM k3l_channel_fids as ch
        WHERE
            channel_id = $1 
            AND 
            compute_ts=(select max(compute_ts) from k3l_channel_fids where channel_id=$1)
            AND 
            fid = ANY($2::integer[])
        ORDER BY rank
        """
    else:
        sql_query = """
        WITH total AS (
            SELECT count(*) as total from k3l_channel_fids 
            WHERE channel_id = $1
            AND compute_ts=(select max(compute_ts) from k3l_channel_fids where channel_id=$1)
        ),
        addresses as (
        SELECT '0x' || encode(fids.custody_address, 'hex') as address, fid
        FROM fids
        union all
         SELECT v.claim->>'address' as address, fid
         FROM verifications v 
        ),
        top_records as (
        SELECT
            ch.fid,
            rank,
            score,
            ((total.total - (rank - 1))*100 / total.total) as percentile
        FROM k3l_channel_fids as ch
        CROSS JOIN total
        WHERE
            channel_id = $1 
            AND 
            compute_ts=(select max(compute_ts) from k3l_channel_fids where channel_id=$1)
            AND 
            ch.fid = ANY($2::integer[])
        ORDER BY rank
        ),
        mapped_records as (
        SELECT top_records.*,addresses.address 
        FROM top_records 
        LEFT JOIN addresses using (fid)
        )
        SELECT
        fid,
        any_value(rank) as rank,
        any_value(score) as score,
        any_value(percentile) as percentile,
        ARRAY_AGG(DISTINCT address) as addresses
        FROM mapped_records
        GROUP BY fid
        ORDER by rank

        """
    return await fetch_rows(channel_id, fids, sql_query=sql_query, pool=pool)

async def get_popular_neighbors_casts(
        agg: ScoreAgg,
        weights: Weights,
        trust_scores: list[dict],
        offset: int,
        limit: int,
        lite: bool,
        pool: Pool
):
    match agg:
        case ScoreAgg.RMS:
            agg_sql = 'sqrt(avg(power(fid_cast_scores.cast_score,2)))'
        case ScoreAgg.SUMSQUARE:
            agg_sql = 'sum(power(fid_cast_scores.cast_score,2))'
        case ScoreAgg.SUM | _:
            agg_sql = 'sum(fid_cast_scores.cast_score)'

    resp_fields = "'0x' || encode(casts.hash, 'hex') as cast_hash," \
                  "DATE_TRUNC('hour', casts.timestamp) as cast_hour,"\
                  "casts.fid"
    if not lite:
        resp_fields = f"""
            {resp_fields}, 
            casts.text,
            casts.embeds,
            casts.mentions,
            casts.timestamp,
            cast_score
        """

    sql_query = f"""
        with fid_cast_scores as (
            SELECT
                ci.cast_hash,
                SUM(
                    (
                        ({weights.cast} * trust.v * ci.casted) 
                        + ({weights.reply} * trust.v * ci.replied)
                        + ({weights.recast} * trust.v * ci.recasted)
                        + ({weights.like} * trust.v * ci.liked)
                    )
                    *
                    power(
                        1-(1/(365*24)::numeric),
                        (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - action_ts)) / (60 * 60))::numeric
                    )
                ) as cast_score
            FROM json_to_recordset($1::json)
                AS trust(i int, v numeric) 
            INNER JOIN k3l_cast_action as ci
                ON (ci.fid = trust.i
                    AND ci.action_ts BETWEEN now() - interval '5 days' 
  										AND now() - interval '10 minutes')
            GROUP BY ci.cast_hash, ci.fid
            LIMIT 100000
        )
        , scores AS (
            SELECT
                cast_hash,
                {agg_sql} as cast_score
                FROM fid_cast_scores
                GROUP BY cast_hash
                --    OFFSET $2
                --    LIMIT $3 
            )
    SELECT
        {resp_fields}
    FROM k3l_recent_parent_casts as casts
    INNER JOIN scores on casts.hash = scores.cast_hash 
    WHERE deleted_at IS NULL
    --    ORDER BY casts.timestamp DESC
    ORDER BY cast_hour DESC, scores.cast_score DESC
    OFFSET $2
    LIMIT $3 
    """
    return await fetch_rows(json.dumps(trust_scores), offset, limit, sql_query=sql_query, pool=pool)

async def get_recent_neighbors_casts(
        trust_scores: list[dict],
        offset: int,
        limit: int,
        lite: bool,
        pool: Pool
):
    resp_fields = "'0x' || encode( casts.hash, 'hex') as cast_hash,"\
                  "casts.fid"

    if not lite:
        resp_fields = f"""
            {resp_fields},
            'https://warpcast.com/'||
            fnames.fname||
            '/0x' ||
            substring(encode(casts.hash, 'hex'), 1, 8) as url,
            casts.text,
            casts.embeds,
            casts.mentions,
            casts.timestamp,
            power(
                1-(1/(365*24)::numeric),
                (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - casts.timestamp)) / (60 * 60))::numeric
            )* trust.score as cast_score
        """
    sql_query = f"""
        SELECT
            {resp_fields}
        FROM k3l_recent_parent_casts as casts 
        INNER JOIN  json_to_recordset($1::json)
            AS trust(fid int, score numeric) 
                ON casts.fid = trust.fid
        {'LEFT' if lite else 'INNER'} JOIN fnames ON (fnames.fid = casts.fid)
        WHERE deleted_at IS NULL
        ORDER BY casts.timestamp DESC
        OFFSET $2
        LIMIT $3
    """
    return await fetch_rows(json.dumps(trust_scores), offset, limit, sql_query=sql_query, pool=pool)

async def get_popular_channel_casts_lite(
        channel_id: str,
        channel_url: str,
        agg: ScoreAgg,
        weights: Weights,
        offset: int,
        limit: int,
        sorting_order: str,
        pool: Pool
):
    match agg:
        case ScoreAgg.RMS:
            agg_sql = 'sqrt(avg(power(fid_cast_scores.cast_score,2)))'
        case ScoreAgg.SUMSQUARE:
            agg_sql = 'sum(power(fid_cast_scores.cast_score,2))'
        case ScoreAgg.SUM | _:
            agg_sql = 'sum(fid_cast_scores.cast_score)'

    if sorting_order == 'recent':
        ordering = True
    else:
        ordering = False

    sql_query = f"""
        with fid_cast_scores as (
            SELECT
                hash as cast_hash,
                casts.fid,
                SUM(
                    (
                        ({weights.cast} * fids.score * ci.casted) 
                        + ({weights.reply} * fids.score * ci.replied)
                        + ({weights.recast} * fids.score * ci.recasted)
                        + ({weights.like} * fids.score * ci.liked)
                    )
                    *
                    power(
                        1-(1/(365*24)::numeric),
                        (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ci.action_ts)) / (60 * 60))::numeric
                    )
                ) as cast_score,
                MIN(ci.action_ts) as cast_ts
            FROM k3l_recent_parent_casts as casts 
            INNER JOIN k3l_cast_action as ci
                ON (ci.cast_hash = casts.hash
                    AND ci.action_ts BETWEEN now() - interval '30 days' 
  										AND now() - interval '10 minutes'
                    AND casts.root_parent_url = $2)
            INNER JOIN k3l_channel_rank as fids ON (fids.channel_id=$1 AND fids.fid = ci.fid )
            WHERE deleted_at IS NULL
            GROUP BY casts.hash, casts.fid
            ORDER BY cast_ts desc
            LIMIT 100000
        )
        , scores AS (
            SELECT
                cast_hash,
                fid,
                {agg_sql} as cast_score,
                MIN(cast_ts) as cast_ts
            FROM fid_cast_scores
            GROUP BY cast_hash, fid
        ),
    cast_details as (
    SELECT
        fid,
        '0x' || encode(cast_hash, 'hex') as cast_hash,
        DATE_TRUNC('hour', cast_ts) as cast_hour,
        cast_ts,
        row_number() over(partition by date_trunc('day',cast_ts) order by random()) as rn
    FROM scores
    WHERE cast_score*100000000000>100
    ORDER BY date_trunc('day',cast_ts) DESC, cast_score DESC
    OFFSET $3
    LIMIT $4
    )
    select fid, cast_hash, cast_hour, cast_ts from cast_details
    {'order by cast_ts desc' if ordering else ''}
    """
    return await fetch_rows(channel_id, channel_url, offset, limit, sql_query=sql_query, pool=pool)

async def get_popular_channel_casts_heavy(
        channel_id: str,
        channel_url: str,
        agg: ScoreAgg,
        weights: Weights,
        offset: int,
        limit: int,
        sorting_order: str,
        pool: Pool
):
    match agg:
        case ScoreAgg.RMS:
            agg_sql = 'sqrt(avg(power(fid_cast_scores.cast_score,2)))'
        case ScoreAgg.SUMSQUARE:
            agg_sql = 'sum(power(fid_cast_scores.cast_score,2))'
        case ScoreAgg.SUM | _:
            agg_sql = 'sum(fid_cast_scores.cast_score)'

    if sorting_order == 'recent':
        ordering = True
    else:
        ordering = False

    sql_query = f"""
        with fid_cast_scores as (
            SELECT
                hash as cast_hash,
                SUM(
                    (
                        ({weights.cast} * fids.score * ci.casted) 
                        + ({weights.reply} * fids.score * ci.replied)
                        + ({weights.recast} * fids.score * ci.recasted)
                        + ({weights.like} * fids.score * ci.liked)
                    )
                    *
                    power(
                        1-(1/(365*24)::numeric),
                        (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ci.action_ts)) / (60 * 60))::numeric
                    )
                ) as cast_score,
                MIN(ci.action_ts) as cast_ts
            FROM k3l_recent_parent_casts as casts 
            INNER JOIN k3l_cast_action as ci
                ON (ci.cast_hash = casts.hash
                    AND ci.action_ts BETWEEN now() - interval '30 days' 
  										AND now() - interval '10 minutes'
                    AND casts.root_parent_url = $2)
            INNER JOIN k3l_channel_rank as fids ON (fids.channel_id=$1 AND fids.fid = ci.fid )
            WHERE deleted_at IS NULL
            GROUP BY casts.hash
            ORDER BY cast_ts desc
            LIMIT 100000
        )
        , scores AS (
            SELECT
                cast_hash,
                {agg_sql} as cast_score
                FROM fid_cast_scores
                GROUP BY cast_hash
            ),
    cast_details as (
    SELECT
        '0x' || encode(casts.hash, 'hex') as cast_hash,
        DATE_TRUNC('hour', casts.timestamp) as cast_hour,
        casts.text,
        casts.embeds,
        casts.mentions,
        casts.fid,
        casts.timestamp,
        cast_score,
        row_number() over(partition by date_trunc('day',casts.timestamp) order by random()) as rn
    FROM k3l_recent_parent_casts as casts
    INNER JOIN scores on casts.hash = scores.cast_hash 
    WHERE cast_score*100000000000>100
    ORDER BY date_trunc('day',casts.timestamp) DESC, cast_score DESC
    OFFSET $3
    LIMIT $4
    )
    select cast_hash, cast_hour, text, embeds, mentions, fid, timestamp, cast_score
    from cast_details
    {'order by timestamp desc' if ordering else ''}
    """
    return await fetch_rows(channel_id, channel_url, offset, limit, sql_query=sql_query, pool=pool)


async def get_trending_casts_lite(
        agg: ScoreAgg,
        weights: Weights,
        score_threshold_multiplier:int,
        offset: int,
        limit: int,
        pool: Pool
):
    match agg:
        case ScoreAgg.RMS:
            agg_sql = 'sqrt(avg(power(fid_cast_scores.cast_score,2)))'
        case ScoreAgg.SUMSQUARE:
            agg_sql = 'sum(power(fid_cast_scores.cast_score,2))'
        case ScoreAgg.SUM | _:
            agg_sql = 'sum(fid_cast_scores.cast_score)'

    sql_query = f"""
        with
        latest_global_rank as (
        select profile_id as fid, score from k3l_rank g where strategy_id=3
            and date in (select max(date) from k3l_rank)
            and rank <= 15000
        ),
        fid_cast_scores as (
            SELECT
                hash as cast_hash,
                casts.fid,
                SUM(
                    (
                        ({weights.cast} * fids.score * ci.casted)
                        + ({weights.reply} * fids.score * ci.replied)
                        + ({weights.recast} * fids.score * ci.recasted)
                        + ({weights.like} * fids.score * ci.liked)
                    )
                    *
                    power(
                        1-(1/(365*24)::numeric),
                        (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ci.action_ts)) / (60 * 60))::numeric
                    )
                ) as cast_score,
                MIN(ci.action_ts) as cast_ts
            FROM k3l_recent_parent_casts as casts
            INNER JOIN k3l_cast_action as ci
                ON (ci.cast_hash = casts.hash
                    AND ci.action_ts BETWEEN now() - interval '3 days'
  										AND now() - interval '10 minutes')
            INNER JOIN latest_global_rank as fids ON (fids.fid = ci.fid )
            GROUP BY casts.hash, casts.fid
            ORDER BY cast_ts desc
            LIMIT 100000
        )
        , scores AS (
            SELECT
                fid,
                cast_hash,
                {agg_sql} as cast_score,
                MIN(cast_ts) as cast_ts
            FROM fid_cast_scores
            GROUP BY cast_hash, fid
        ),
    cast_details as (
    SELECT
        fid,
        '0x' || encode(cast_hash, 'hex') as cast_hash,
        DATE_TRUNC('hour', cast_ts) as cast_hour,
        row_number() over(partition by date_trunc('hour',cast_ts) order by random()) as rn
    FROM scores
    WHERE cast_score*{score_threshold_multiplier}>1
    ORDER BY  cast_hour DESC,cast_score DESC
    OFFSET $1
    LIMIT $2)
    select fid, cast_hash,cast_hour from cast_details order by rn
    """
    return await fetch_rows(offset, limit, sql_query=sql_query, pool=pool)


async def get_top_casters(
        offset: int,
        limit: int,
        pool: Pool
):
    sql_query = """ select i as fid, v as score from k3l_top_casters 
                    where date_iso = (select max(date_iso) from k3l_top_casters)
                    order by v desc
                    OFFSET $1 LIMIT $2"""
    return await fetch_rows(offset, limit, sql_query=sql_query, pool=pool)


async def get_top_spammers(
        offset: int,
        limit: int,
        pool: Pool
):
    sql_query = """ select 
                    fid,
                    display_name,
                    total_outgoing,
                    spammer_score,
                    total_parent_casts,
                    total_replies_with_parent_hash,
                    global_openrank_score,
                    global_rank,
                    total_global_rank_rows
                    from k3l_top_spammers 
                    where date_iso = (select max(date_iso) from k3l_top_spammers)
                    order by global_rank
                    OFFSET $1 LIMIT $2"""
    return await fetch_rows(offset, limit, sql_query=sql_query, pool=pool)