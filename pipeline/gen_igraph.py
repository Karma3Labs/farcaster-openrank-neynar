# standard dependencies
from pathlib import Path
import argparse
import logging
import os

# local dependencies
import utils
from config import Config
from timer import Timer

# 3rd party dependencies
import igraph as ig
import pandas as pd
import numpy as np

def main(incsv:Path,  outdir:Path, prefix:str, logger:logging.Logger):
  with Timer(name="read_csv"):
    edges_df = pd.read_csv(incsv)
    stacked = edges_df[['i','j']].stack()
    edges_df[['i_code', 'j_code']] = pd.Series(stacked.factorize()[0], index=stacked.index).unstack()
  logger.info(utils.df_info_to_string(edges_df, with_sample=True))
  with Timer(name="df_to_igraph"):
    g = ig.Graph.DataFrame(edges_df, directed=True, use_vids=False)
  logger.info(ig.summary(g))
  with Timer(name="write_pickle"):
    dfile = os.path.join(outdir, f"{prefix}_df.pkl")
    gfile = os.path.join(outdir, f"{prefix}_ig.pkl")
    logger.info(f"Saving dataframe to {dfile}  and graph to {gfile}")
    edges_df.to_pickle(dfile)
    g.write_pickle(gfile)


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument("-i", "--incsv",
                      help="input localtrust csv file",
                      required=True,
                      type=lambda f: Path(f).expanduser().resolve())  
  parser.add_argument("-o", "--outdir",
                    help="output directory for pickle files",
                    required=True,
                    type=lambda f: Path(f).expanduser().resolve())
  parser.add_argument("-p", "--prefix",
                    help="file prefixes for pickle files",
                    required=True,
                    type=str)
  args = parser.parse_args()
  print(args)
  print(Config.__dict__)

  logger = logging.getLogger()
  utils.setup_filelogger(logger, __file__)
  logger.setLevel(logging.DEBUG)
  utils.setup_consolelogger(logger)

  main(incsv=args.incsv, outdir=args.outdir, prefix=args.prefix, logger=logger)