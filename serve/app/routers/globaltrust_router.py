from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, HTTPException
from loguru import logger
from asyncpg.pool import Pool

from ..models.graph_model import GraphType
from ..dependencies import  db_pool, db_utils
from ..models.score_model import EngagementType, engagement_ids

router = APIRouter(tags=["Global OpenRank Scores"])

@router.get("/following/rankings")
async def get_top_following_profiles(
  offset: Annotated[int | None, Query()] = 0,
  limit: Annotated[int | None, Query(le=1000)] = 100,
  pool: Pool = Depends(db_pool.get_db)
):
  """
  Get a list of fids based on the follows relationships in the Fracaster network
    and scored by Eigentrust algorithm. \n
  This API takes two optional parameters - offset and limit. \n
  By default, limit is 100 and offset is 0 i.e., returns top 100 fids.
  """
  ranks = await db_utils.get_top_profiles(strategy_id=GraphType.following.value, 
                                          offset=offset, 
                                          limit=limit, 
                                          pool=pool)
  return {"result": ranks}

@router.get("/engagement/rankings")
async def get_top_engagement_profiles(
  engagement_type: Annotated[EngagementType, Query()] = EngagementType.V1,
  offset: Annotated[int | None, Query()] = 0,
  limit: Annotated[int | None, Query(le=1000)] = 100,
  pool: Pool = Depends(db_pool.get_db)
):
  """
  Get a list of fids based on the engagement relationships in the Fracaster network
    and scored by Eigentrust algorithm. \n
  This API takes two optional parameters - offset and limit. \n
  By default, limit is 100 and offset is 0 i.e., returns top 100 fids.
  """
  if engagement_type == EngagementType.V1:
      strategy_id = engagement_ids[EngagementType.V1]
  elif engagement_type == EngagementType.V3:
      strategy_id = engagement_ids[EngagementType.V3]

  ranks = await db_utils.get_top_profiles(strategy_id=strategy_id,
                                          offset=offset, 
                                          limit=limit, 
                                          pool=pool)
  return {"result": ranks}

@router.post("/following/fids")
async def get_following_rank_for_fids(
  fids: Annotated[list[int], Body(
    title="Farcaster IDs",
    description="A list of FIDs.",
    examples=[
      [1,2,3]
    ]
  )],
  pool: Pool = Depends(db_pool.get_db)
):
  """
  Given a list of input fids, return a list of fids
    that are ranked based on the follows relationships in the Fracaster network
    and scored by Eigentrust algorithm. \n
    Example: [1, 2] \n
  """
  if not (1 <= len(fids) <= 100):
    raise HTTPException(status_code=400, detail="Input should have between 1 and 100 entries")
  ranks = await db_utils.get_profile_ranks(strategy_id=GraphType.following.value, 
                                           fids=fids, 
                                           pool=pool)
  return {"result": ranks}


@router.post("/engagement/fids")
async def get_engagement_rank_for_fids(
  fids: Annotated[list[int], Body(
    title="Farcaster IDs",
    description="A list of FIDs.",
    examples=[
      [1,2,3]
    ]
  )],
  engagement_type: Annotated[EngagementType, Query()] = EngagementType.V1,
  pool: Pool = Depends(db_pool.get_db)
):
  """
  Given a list of input fids, return a list of fids
    that are ranked based on the engagement relationships in the Fracaster network
    and scored by Eigentrust algorithm. \n
    Example: [1, 2] \n
  """
  if not (1 <= len(fids) <= 100):
    raise HTTPException(status_code=400, detail="Input should have between 1 and 100 entries")

  if engagement_type == EngagementType.V1:
      strategy_id = engagement_ids[EngagementType.V1]
  elif engagement_type == EngagementType.V3:
      strategy_id = engagement_ids[EngagementType.V3]

  ranks = await db_utils.get_profile_ranks(strategy_id=strategy_id,
                                           fids=fids, 
                                           pool=pool)
  return {"result": ranks}


