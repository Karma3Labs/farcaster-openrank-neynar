from enum import Enum

class Channel(Enum):
  degen = 'degen'
  base = 'base'
  optimisim = 'optimisim'
  founders = 'founders'
  farcaster = 'farcaster'

CHANNEL_URLS = dict()
CHANNEL_URLS[Channel.degen] = 'chain://eip155:7777777/erc721:0x5d6a07d07354f8793d1ca06280c4adf04767ad7e'
CHANNEL_URLS[Channel.base] = 'https://onchainsummer.xyz'
CHANNEL_URLS[Channel.optimisim] = 'https://warpcast.com/~/channel/optimism'
CHANNEL_URLS[Channel.founders] = 'https://farcaster.group/founders'
CHANNEL_URLS[Channel.farcaster] = 'chain://eip155:7777777/erc721:0x4f86113fc3e9783cf3ec9a552cbb566716a57628'