"""
Implements a parser for the Bencoding format as described at
https://wiki.theory.org/BitTorrentSpecification#Bencoding
"""
import re

intNonRe = re.compile(rb'i(0|-?[1-9][0-9]*)e')
bytesHeadRe = re.compile(rb'(0|[1-9][0-9]*):')

def parseBencodingBytes(b):
  pos, bLen = 0, len(b)
  while pos < bLen:
    value, pos = _parseBencodedValue(b, pos)
    yield value

def _matchAndAdvance(b, pos, tokenRe):
  match = tokenRe.match(b, pos)
  if match is None:
    return False, pos, None
  return True, pos + len(match.group(0)), match.group(1)

def _checkDictKey(pos, k):
  if isinstance(k, list):
      msg = 'Tried to use a list as key in a dict (pos: {0}, key: {1})!'
      raise TypeError(msg.format(pos, k))
  if isinstance(k, dict):
      msg = 'Tried to use a dict as key in a dict (pos: {0}, key: {1})!'
      raise TypeError(msg.format(pos, k))
  return k

def _parseBencodedValue(b, pos):

  found, pos, tokenVal = _matchAndAdvance(b, pos, intNonRe)
  if found:
    return int(tokenVal), pos

  found, pos, tokenVal = _matchAndAdvance(b, pos, bytesHeadRe)
  if found:
    bytesLen = int(tokenVal)
    if pos + bytesLen > len(b):
      msg = ('Byte string starting at {0} is longer than the remaining tail'
      + ' of the encoded data (bytestring length: {1}, remaining: {2})!')
      raise ValueError(msg.format(pos, bytesLen, len(b) - pos))
    posStart = pos
    pos += bytesLen
    return b[posStart:pos], pos

  if b.startswith(b'l', pos):
    elements, pos = _parseBencodedList(b, pos=pos + 1)
    return [e for _p, e in elements], pos

  if b.startswith(b'd', pos):
    oldPos = pos
    elements, pos = _parseBencodedList(b, pos=pos + 1)
    if len(elements) % 2 != 0:
      msg = ('Encoded data for dictionary with elements starting at {0}'
      + ' contains uneven count of elements ({1})!')
      raise ValueError(msg.format(oldPos, len(elements)))
    keys, values = elements[::2], elements[1::2]
    return {_checkDictKey(*k): v[1] for k, v in zip(keys, values)}, pos

  msg = 'Unrecognized content at {0}!'
  raise ValueError(msg.format(pos))

def _parseBencodedList(b, pos):
  values = []
  while True:

    if b.startswith(b'e', pos):
      return values, pos + 1

    oldPos = pos
    value, pos = _parseBencodedValue(b, pos) # Fails if no value at pos
    values.append((oldPos, value))
