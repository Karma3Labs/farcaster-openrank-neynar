import itertools
import time
from typing import Annotated
import json

from fastapi import APIRouter, Depends, Query, HTTPException
from loguru import logger

from ..dependencies.graph import get_engagement_graph, get_following_graph
from ..models.graph_model import Graph

router = APIRouter(tags=["graphs"])

async def fetch_korder_neighbors(
  addresses: list[str],
  graph: Graph,        
  max_degree: Annotated[int, Query(le=5)] = 2,
  max_neighbors: Annotated[int | None, Query(le=1000)] = 100,
) -> list :
  try:
    klists = []
    mindist_and_order = 1
    limit = max_neighbors
    while mindist_and_order <= max_degree:
        neighbors = graph.graph.neighborhood(
            addresses, order=mindist_and_order, mode="out", mindist=mindist_and_order
        )
        klists.append(graph.graph.vs[neighbors[0][:limit]]["name"])
        limit = limit - len(neighbors[0])
        if limit <= 0:
            break # we have reached limit of neighbors
        mindist_and_order += 1
    # end of while
    return list(itertools.chain(*klists))
  except ValueError:
    raise HTTPException(status_code=404, detail="Neighbors not found")

async def get_neighbors_edges(  addresses: list[str],
  graph: Graph,        
  max_degree: Annotated[int, Query(le=5)] = 2,
  max_neighbors: Annotated[int | None, Query(le=1000)] = 100,
) -> str: 
  start_time = time.perf_counter()
  neighbors = await fetch_korder_neighbors(addresses, graph, max_degree, max_neighbors)
  logger.info(f"graph took {time.perf_counter() - start_time} secs")
  logger.debug(neighbors)
  start_time = time.perf_counter()
  res = graph.df[graph.df['i'].isin(neighbors) & graph.df['j'].isin(neighbors)].to_json(orient="records")
  logger.info(f"dataframe took {time.perf_counter() - start_time} secs")
  return res

@router.get("/neighbors/engagement")
async def get_neighbors_engagement(
  addresses: list[str],
  k: Annotated[int, Query(le=5)] = 2,
  limit: Annotated[int | None, Query(le=1000)] = 100,
  graph: Graph = Depends(get_engagement_graph),
):
  logger.debug(addresses)
  res = await get_neighbors_edges(addresses, graph, k, limit)
  return {"result": json.loads(res)}

@router.get("/neighbors/following")
async def get_neighbors_following(
  addresses: list[str],
  k: Annotated[int, Query(le=5)] = 2,
  limit: Annotated[int | None, Query(le=1000)] = 100,
  graph: Graph = Depends(get_following_graph),
):
  logger.debug(addresses)
  res = await get_neighbors_edges(addresses, graph, k, limit)
  return {"result": json.loads(res)}