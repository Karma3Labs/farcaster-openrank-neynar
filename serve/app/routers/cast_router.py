from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException
from loguru import logger
from asyncpg.pool import Pool

from ..models.graph_model import Graph
from ..models.score_model import ScoreAgg, Weights
from ..dependencies import graph, db_pool, db_utils
from ..config import settings

router = APIRouter(tags=["Casts"])

# turning off this API due to SQL query latency issues.
@router.get("/personalized/popular/{fid}")
async def get_casts_for_fid(
  fid: int,
  agg: Annotated[ScoreAgg | None, 
                 Query(description="Define the aggregation function"\
                       " - `rms`, `sumsquare`, `sum`")] = ScoreAgg.SUM_SQ,
  weights: Annotated[str | None, Query()] = 'L1C10R5Y7',
  k: Annotated[int, Query(le=5)] = 2,
  limit: Annotated[int | None, Query(le=1000)] = 100,
  pool: Pool = Depends(db_pool.get_db),
  graph_model: Graph = Depends(graph.get_engagement_graph),
):
  """
  Under construction. **NOT FOR PRODUCTION USE**\n
  \n\n
    Get a list of casts that have been interacted with the most
    in a user's extended network. \n
  This API takes four optional parameters - 
    agg, weights, k,  and limit. \n
  Parameter 'agg' is used to define the aggregation function and 
    can take any of the following values - `rms`, `sumsquare`, `sum`. \n
  Parameter 'weights' is used to define the weights to be assigned
    to (L)ikes, (C)asts, (R)ecasts and repl(Y) actions by profiles. \n
  Parameter 'k' is used to constrain the social graph to k-degrees of separation. \n
  Parameter 'limit' is used to specify the number of results to return. \n
  By default, agg=sumsquare, weights='L1C10R5Y7', k=2, and limit=100
    i.e., returns recent 100 popular casts.

  """
  try:
    weights = Weights.from_str(weights)
  except:
    raise HTTPException(status_code=400, detail="Weights should be of the form 'LxxCxxRxx'")

  # compute eigentrust on the neighbor graph using fids
  trust_scores = await graph.get_neighbors_scores([fid], graph_model, k, limit)
  # trust_scores = sorted(trust_scores, key=lambda d: d['score'], reverse=True)

  casts = await db_utils.get_popular_neighbors_casts(agg,
                                               weights,
                                               trust_scores=trust_scores,
                                               limit=limit,
                                               pool=pool)
  return {"result": casts}


@router.get("/personalized/recent/{fid}")
async def get_casts_for_fid(
  fid: int,
  k: Annotated[int, Query(le=5)] = 2,
  offset: Annotated[int | None, Query()] = 0,
  limit: Annotated[int | None, Query(le=1000)] = 100,
  pool: Pool = Depends(db_pool.get_db),
  graph_model: Graph = Depends(graph.get_engagement_graph),
):
  """
  Under construction. **NOT FOR PRODUCTION USE**\n
  \n\n
    Get a list of casts that have been casted by the 
      popular profiles in a user's extended network. \n
  This API takes three optional parameters - 
    k, offset  and limit. \n
  Parameter 'k' is used to constrain the social graph to k-degrees of separation. \n
  Parameter 'offset' is used to specify how many results to skip 
    and can be useful for paginating through results. \n
  Parameter 'limit' is used to specify the number of results to return. \n
  By default, k=2, offset=0, and limit=100
    i.e., returns recent 100 frame urls casted by extended network.
  """
  # compute eigentrust on the neighbor graph using fids
  trust_scores = await graph.get_neighbors_scores([fid], graph_model, k, limit)

  casts = await db_utils.get_recent_neighbors_casts(
                                               trust_scores=trust_scores,
                                               offset=offset,
                                               limit=limit,
                                               pool=pool)
  casts = sorted(casts, key=lambda d: d['score'], reverse=True)
  return {"result": casts}

# @router.post("/channel/{channel_id}")
# async def get_casts_by_channel_id(
#   channel_id: str,
#   k: int,
#   limit: int,
#   pool: Pool = Depends(db_pool.get_db),
#   graph_model: Graph = Depends(graph.get_engagement_graph),
#   agg: Annotated[ScoreAgg | None, Query()] = ScoreAgg.SUM_SQ,
#   weights: Annotated[str | None, Query()] = 'L1C10R5',
# ):
#   """

#   """
#   try:
#     weights = Weights.from_str(weights)
#   except:
#     raise HTTPException(status_code=400, detail="Weights should be of the form 'LxxCxxRxx'")

#   follower_fids = fetch_channel_followers(channel_id)
#   # compute eigentrust on the neighbor graph using fids
#   trust_scores = await graph.get_neighbors_scores(follower_fids, graph_model, k, limit)
#   frames = await db_utils.get_ranked_casts_from_channel(channel_id, agg,
#                                                weights,
#                                                trust_scores=trust_scores,
#                                                limit=limit,
#                                                pool=pool)
#   return {"result": frames}
