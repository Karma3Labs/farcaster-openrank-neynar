from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException
from loguru import logger
from asyncpg.pool import Pool

from ..models.graph_model import PlGraph
from ..models.score_model import ScoreAgg, Weights
from ..dependencies import db_pool, db_utils, pl_graph_utils
from ..config import settings

router = APIRouter(tags=["Casts"])

@router.get("/personalized/popular/{fid}")
async def get_popular_casts_for_fid(
  fid: int,
  agg: Annotated[ScoreAgg | None, 
                 Query(description="Define the aggregation function"\
                       " - `rms`, `sumsquare`, `sum`")] = ScoreAgg.SUMSQUARE,
  weights: Annotated[str | None, Query()] = 'L1C10R5Y1',
  k: Annotated[int, Query(le=5)] = 1,
  offset: Annotated[int | None, Query()] = 0,
  limit: Annotated[int | None, Query(le=50)] = 25,
  graph_limit: Annotated[int | None, Query(le=1000)] = 100,
  lite: Annotated[bool, Query()] = True,
  pool: Pool = Depends(db_pool.get_db),
  graph_model: PlGraph = Depends(pl_graph_utils.get_engagement_graph),
):
  """
    Get a list of casts that have been interacted with the most
    in a user's extended network. \n
  This API takes optional parameters - 
    agg, weights, k, offset, limit  and lite. \n
  Parameter 'agg' is used to define the aggregation function and 
    can take any of the following values - `rms`, `sumsquare`, `sum`. \n
  Parameter `weights` is used to define the weights to be assigned
    to (L)ikes, (C)asts, (R)ecasts and repl(Y) actions by profiles. \n
  Parameter 'k' is used to constrain the social graph to k-degrees of separation. \n
  Parameter 'lite' is used to constrain the result to just cast hashes. \n
  Parameter 'offset' is used to specify how many results to skip 
    and can be useful for paginating through results. \n
  Parameter 'limit' is used to specify the number of results to return. \n
  Parameter 'graph_limit' is used to constrain the graph neighborhood. \n
  By default, agg=sumsquare, weights='L1C10R5Y1', k=1, offset=0, 
    limit=25, graph_limit=100 and lite=true
    i.e., returns recent 25 popular casts.
  """
  try:
    weights = Weights.from_str(weights)
  except:
    raise HTTPException(status_code=400, detail="Weights should be of the form 'LxxCxxRxx'")

  # compute eigentrust on the neighbor graph using fids
  trust_scores = await pl_graph_utils.get_neighbors_scores(fid, graph_model, k, graph_limit)

  logger.trace(f"trust scores:{trust_scores}")


  casts = await db_utils.get_popular_neighbors_casts(agg,
                                               weights,
                                               trust_scores=trust_scores,
                                               offset=offset,
                                               limit=limit,
                                               lite=lite,
                                               pool=pool)
  return {"result": casts}


@router.get("/personalized/recent/{fid}")
async def get_recent_casts_for_fid(
  fid: int,
  k: Annotated[int, Query(le=5)] = 1,
  offset: Annotated[int | None, Query()] = 0,
  limit: Annotated[int | None, Query(le=50)] = 25,
  graph_limit: Annotated[int | None, Query(le=1000)] = 100,
  lite: Annotated[bool, Query()] = True,
  pool: Pool = Depends(db_pool.get_db),
  graph_model: PlGraph = Depends(pl_graph_utils.get_engagement_graph),
):
  """
    Get a list of casts that have been casted by the 
      popular profiles in a user's extended network. \n
  This API takes optional parameters - 
    k, offset, limit, graph_limit and lite. \n
  Parameter 'k' is used to constrain the social graph to k-degrees of separation. \n
  Parameter 'offset' is used to specify how many results to skip 
    and can be useful for paginating through results. \n
  Parameter 'limit' is used to specify the number of results to return. \n
  Parameter 'graph_limit' is used to constrain the graph neighborhood. \n
  Parameter 'lite' is used to constrain the result to just cast hashes. \n
  By default, k=1, offset=0, limit=25, graph_limit=100 and lite=true
    i.e., returns recent 25 frame urls casted by extended network.
  """
  # compute eigentrust on the neighbor graph using fids
  trust_scores = await pl_graph_utils.get_neighbors_scores(fid, graph_model, k, graph_limit)

  logger.trace(f"trust scores:{trust_scores}")

  casts = await db_utils.get_recent_neighbors_casts(
                                               trust_scores=trust_scores,
                                               offset=offset,
                                               limit=limit,
                                               lite=lite,
                                               pool=pool)
  if not lite:
    casts = sorted(casts, key=lambda d: d['cast_score'], reverse=True)
  return {"result": casts}


@router.get("/global/trending")
async def get_trending_casts(
        agg: Annotated[ScoreAgg | None,
                 Query(description="Define the aggregation function"\
                       " - `rms`, `sumsquare`, `sum`")] = ScoreAgg.SUMSQUARE,
        weights: Annotated[str | None, Query()] = 'L1C10R5Y1',
        offset: Annotated[int | None, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(ge=0, le=5000)] = 100,
        pool: Pool = Depends(db_pool.get_db)
):
    """
    Get a list of casts that have been cast by the
      popular profiles in a user's extended network. \n
  This API takes optional parameters -
    agg, weights, offset, limit and lite. \n
  Parameter 'agg' is used to define the aggregation function and
    can take any of the following values - `rms`, `sumsquare`, `sum`. \n
  Parameter 'weights' is used to define the weights to be assigned
    to (L)ikes, (C)asts, (R)ecasts and repl(Y) actions by profiles. \n
  Parameter 'score_mask' is used to define how many decimal places to consider
    when deciding whether or not to show a cast.
    The lower this number the higher the score that a cast needs to have
    to be included in the feed. \n
  Parameter 'lite' is used to constrain the result to just cast hashes. \n
  Parameter 'offset' is used to specify how many results to skip
    and can be useful for paginating through results. \n
  Parameter 'limit' is used to specify the number of results to return. \n
  By default, agg=sumsquare, weights='L1C10R5Y1', score_mask=6, offset=0,
    limit=25, and lite=true
    i.e., returns recent 100 popular casts whose score is greater than 1e-6.
  """
    # compute eigentrust on the neighbor graph using fids
    try:
        weights = Weights.from_str(weights)
    except:
        raise HTTPException(status_code=400, detail="Weights should be of the form 'LxxCxxRxx'")

    casts = await db_utils.get_trending_casts_lite(
            agg=agg,
            weights=weights,
            score_threshold_multiplier=pow(10,5),
            offset=offset,
            limit=limit,
            pool=pool)

    return {"result": casts}

