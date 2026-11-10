import torch
import numpy as np
from collections import defaultdict
from music21 import *
from scoreProcessing import*
from fractions import Fraction

def partToChannel(part,stepsPerQuarter=12,pitchLow=0,pitchHigh=127):
    """
    Converts a single music21 part into a 2D piano roll (channel).
    """
    flat = part.stripTies(inPlace=False).flatten()
    totalQuarters = float(flat.highestTime)
    nSteps = int(np.ceil(totalQuarters * stepsPerQuarter)) + 1
    nPitches = pitchHigh - pitchLow + 1
    roll = np.zeros((nPitches, nSteps), dtype=np.uint8)
    onsets = np.zeros_like(roll)
    for el in flat.notes:
        ql = float(el.duration.quarterLength)
        if el.duration.isGrace or ql <= 0:
            continue
        start = int(round(float(el.offset) * stepsPerQuarter))
        end = int(round((float(el.offset) + ql) * stepsPerQuarter))
        #make sure end is at least one after the start
        end = max(end, start + 1)
        #make sure not out of bounds
        end = min(end, nSteps)
        pitches = el.pitches if isinstance(el, chord.Chord) else (el.pitch,)
        for p in pitches:
            #row is the appropriate pitch
            row = int(p.midi) - pitchLow
            if 0 <= row < nPitches:
                roll[row, start:end] = 1

                onsets[row, start] = 1
    return onsets, roll

def channelToPart(channelRoll,channelOnsets,stepsPerQuarter=12,pitchLow=0,pitchHigh=127):
    part = stream.Part()
    nPitches,nSteps=channelRoll.shape
    for row in range(nSteps):
        alreadyInserted=False
        for col in range(nPitches):
            if channelOnsets[col, row] and not alreadyInserted:
                end = row + 1
                while end < nSteps and channelRoll[col, end] and not channelOnsets[col, end]:
                    end += 1
                pitch = col + pitchLow
                el = note.Note(pitch)
                el.quarterLength = Fraction(end - row, stepsPerQuarter)
                part.insert(Fraction(row, stepsPerQuarter), el)
                #ensures only one note at each section
                alreadyInserted=True 
                row = end
    return part

def getAllChannels(score, stepsPerQuarter=12, pitchLow=0, pitchHigh=127):
    """returns a list of tuples, each tuple contains onsets then roll"""
    channels = set()
    for part in score.parts:
        channelOnsets, channelRoll = partToChannel(part, stepsPerQuarter, pitchLow, pitchHigh)
        channels.add((channelOnsets.tobytes(), channelRoll.tobytes()))
    return channels











  


     
  
s = converter.parse("mozart40.mxl")
getAllParts(s)
removeUnpitched(s)
transpose_transposing_instruments(s)
channels = getAllChannels(s)







