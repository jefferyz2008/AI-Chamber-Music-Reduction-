"""this file contains all the heuristics I will use to determine if a 
line is worth keeping in the score or cutting"""
from music21 import*
from instruments import*
from math import log2
from collections import Counter
from slidingFrame import*
from fractions import Fraction

def nthMeasure(part,n):
    """returns the nth measure of part"""
    return part.getElementsByClass('Measure')[n-1] #0th measure becomes first

def topNote(el):
    """Highest note of a chord, or the note itself."""
    return max(el.notes, key=lambda n: n.pitch.ps) if el.isChord else el


def is_new_attack(tie):
        # No tie object -> normal, un-tied note -> counts.
        # tie.type == 'start' -> first sounded note of the tie -> counts.
        # tie.type in ('continue', 'stop') -> same sustained note -> skip.
        return not tie or tie.type == 'start'
 

def pitchCount(frame, length=None):
    center=frame.duration.quarterLength/2
    count = Counter()
    for el in frame.flatten().notes:
        if el.duration.isGrace:
            continue
        n = max(el.notes, key=lambda n: n.pitch.ps) if el.isChord else el
        if not is_new_attack(n.tie):
            continue
        w = 1 if center is None else getWeight(el, frame)
        count[n.pitch.midi] += w
    return count
 
def ioiCount(frame,length=None):
    count=Counter()
    center=frame.duration.quarterLength/2
    frame=frame.flatten()
    allNotes=frame.notes
    if not allNotes:
        return Counter([])
    lastOffset=allNotes[0].offset
    for index in range(1,len(allNotes)):
        currentNote=frame.notes[index]
        if not is_new_attack(currentNote.tie):
            continue
        if currentNote.duration.isGrace:
            continue
        currentIOI=currentNote.offset-lastOffset
     
        lastOffset+=currentIOI
        if not currentIOI:
              continue
        w = 1 if center is None else getWeight(currentNote
                                               , frame) 
        count[round(currentIOI,2)]+=w
         
     
    return count
         
        





def wellRoundedHeuristic(frame,weight=1):
    """returns the sum of the 2 entropies"""
    #weight is how much more IOI entropy matters than pitch
    voices=frame.voices
    if not voices:
        return (getPitchEntropy(frame)+getIOIEntropy(frame)*weight)/(weight+1)
    return (sum([getPitchEntropy(voice) for voice in voices])
                +sum([getIOIEntropy(voice)*weight for voice in voices]))/(weight+1)


def getPitchEntropy(frame): 
    """Calculates Shannon Entropy of a measure based on note pitch"""
    #if centered, it calculates a weighted entropy where notes near the center
    #are weighted more
    #center is an int representing the offset from the beginning of the frame
    pitches=pitchCount(frame, 4)
    #this is a counter
    totalNotes=sum(pitches.values())

    if totalNotes<=1:
        return 0
    total=0
    for p in pitches:
        pitch=pitches[p]
        total+=pitch/totalNotes*log2(pitch/totalNotes)
    assert(-total>=0)
    return -1*total
    
 

def getIOIEntropy(frame):
    """Calculates Shannon entropy (bits) of a measure based on time
    between notes."""
    #if centered, it calculates a weighted entropy where notes near the center
    #are weighted more
    #center is an int representing the offset from the beginning of the frame
    IOIs=ioiCount(frame,4)
    totalIntervals=sum(IOIs.values())
 
    if totalIntervals <=1:
        return 0.0
    total=0
    for interval in IOIs:
         
        p=IOIs[interval]/totalIntervals
        total+= p*log2(p)
    assert(-total>=0)
    return -total


 
    
#H(X|Y) = -Σ P(x,y) log₂ P(x|y)
#entropy calculations??
def _attacks(frame):
    """Set of (offset, midi) for each new attack in a frame, with offsets
    measured from the frame's first attack so frames can start anywhere."""
    flat = frame.flatten()
    found = []
    for el in flat.notes:
        if el.duration.isGrace:
            continue
        n = max(el.notes, key=lambda x: x.pitch.ps) if el.isChord else el
        if not is_new_attack(n.tie):
            continue
        offset = Fraction(flat.elementOffset(el)).limit_denominator(12)
        found.append((offset, n.pitch.midi))
    if not found:
        return set()
    first = min(o for o, _ in found)
    return {(round(float(o - first), 4), m) for o, m in found}
 
 
def _jaccard(a, b):
    union = a | b
    return len(a & b) / len(union) if union else 0.0
 
 
def frameSimilarity(frameA, frameB):
    """Returns (noteSimilarity, rhythmSimilarity), both from 0.0 to 1.0.
 
    rhythmSimilarity: share of attack positions the frames have in common.
    noteSimilarity:   share of (position, pitch) pairs the frames have in
                      common, i.e. the same pitch at the same position.
    Note similarity can never exceed rhythm similarity.
    """
    a = _attacks(frameA)
    b = _attacks(frameB)
 
    noteSim = _jaccard(a, b)
    rhythmSim = _jaccard({o for o, _ in a}, {o for o, _ in b})
    return noteSim, rhythmSim