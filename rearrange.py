from music21 import *
from instruments import *
from heuristics import *
from slidingFrame import *
from scoreProcessing import *
import copy
from fractions import Fraction
from functools import lru_cache
from bisect import bisect_left
import statistics
import heapq 
 
 
originalScore = converter.parse("mozart40.mxl")
# Parse the MusicXML file 
  
getAllParts(originalScore)
removeUnpitched(originalScore)
#flattenVoices(originalScore)
transpose_transposing_instruments(originalScore)
 
 
 
 
def getAttackTimes(score, precision=4):
    """Returns a sorted list of every offset (in quarter notes from the start
    of the piece) at which at least one note begins. Simultaneous attacks
    across parts and voices appear once. Rests, grace notes, and tie
    continuations are skipped."""
    flat = score.flatten()
    times = set()
    for el in flat.notes:
        if el.duration.isGrace:
            continue
        if isinstance(el, chord.Chord):
            # same rule as your other functions: the top note's tie decides
            tie = max(el.notes, key=lambda n: n.pitch.ps).tie
        else:
            tie = el.tie
        if not is_new_attack(tie):
            continue
        times.add(round(float(flat.elementOffset(el)), precision))
    return sorted(times)


 
def getScoresDict(score):
    allNotes={}
    allAttacks=getAttackTimes(score)
    for attackTime in allAttacks:
        allNotes[attackTime]={}



def _attacksByTime(flatPart, precision=4):
    """{time: element} for each new attack in an already-flattened part.
    If several notes start together (voices), keeps the one with the highest pitch."""
    attacks = {}
    for el in flatPart.notes:
        if el.duration.isGrace:
            continue
        top = topNote(el)
        if not is_new_attack(top.tie):
            continue
 
        t = round( Fraction(flatPart.elementOffset(el)).limit_denominator(12) , precision)
        if t not in attacks or top.pitch.ps > topNote(attacks[t]).pitch.ps:
     
            attacks[t] = topNote(el) if el.isChord else el
    return attacks
def testUniqueNoteObjects(scoresDict):
    seen = {}

    for attackTime, parts in scoresDict.items():
        for partIndex, (heuristic, note) in parts.items():
            noteID = id(note)
            assert(note.duration)
            assert noteID not in seen, (
                f"Duplicate Note object found!\n"
                f"Object ID: {noteID}\n"
                f"First occurrence: time={seen.get(noteID)}\n"
                f"Second occurrence: time={attackTime}, part={partIndex}\n"
                f"Note: {note}"
            )

            seen[noteID] = (attackTime, partIndex)

    return True

def getScoresDict(score, weight,length=4,precision=4):
    """
    Returns {attackTime: {partIndex: (heuristic, noteObject)}}.
    partIndex 0 is the first part in the score. A part appears under an
    attackTime only if it has a new attack at that time.  
    """
     
    allNotes = {}
    allAttacks = getAttackTimes(score, precision)
 
    # flatten each part once, and index its attacks by time
    flatParts = [p.flatten() for p in score.parts]
    #[{time:element,time2:element2}... for every instrument]
    attackTables = [_attacksByTime(fp, precision) for fp in flatParts]

    for attackTime in allAttacks:
        allNotes[attackTime] = {}
        for i, flatPart in enumerate(flatParts):
            el = attackTables[i].get(attackTime)
 
            if el is None:
             
                   continue   
 
            frame = getFrame(flatPart, length, attackTime)#when it attacks
            
            h = wellRoundedHeuristic(frame,weight)

            allNotes[attackTime][i] = (h, el)
    return allNotes       
 
def getEntropy(score,time,length):
    #returns the total entropy of the whole score at that time
    total=0
    for part in score:
        frame=getFrame(part,length,time)
        eval=wellRoundedHeuristic(frame,2)
        total+=eval
    return total
 
 
#each note has a window with other notes in it.
  
def build_frame(score, start_time, end, scores_dict,beam=5):
    times = sorted(scores_dict)
    def getEntropyAtTimes(d):
                 new={}
                 for time in d:
                     assert(not new.get(time,None))
                     new[time]=getEntropy(score,time,4)
                 return new
    total_entropy = getEntropyAtTimes(times)

    choice = {}   # state -> (next_idx, next_part, next_pitch, note_or_None)

    @lru_cache(maxsize=None)
    def best(idx, prev_part, prev_pitch):
        if idx >= len(times) or times[idx] >= end:
            return 0.0                      # terminal: no choice stored
        
        t = times[idx]

        # option 1: rest, state unchanged
        best_score = best(idx + 1, prev_part, prev_pitch)
        best_move = (idx + 1, prev_part, prev_pitch, None)

        # option 2: take a candidate note
        cands = scores_dict[t].items()
        if prev_pitch is not None:
            cands = heapq.nsmallest(
                beam, cands,
                key=lambda kv: abs(kv[1][1].pitch.midi - prev_pitch))

        for part, (entropy, note) in cands:
            gain = entropy
            if prev_part is not None and part != prev_part:
                gain -= total_entropy[t]

            nxt = bisect_left(times, t + note.duration.quarterLength)
            total = gain + best(nxt, part, note.pitch.midi)
            if total > best_score:
                best_score = total
                best_move = (nxt, part, note.pitch.midi, note)
         
        #the successor of the current state is the best move
        choice[(idx, prev_part, prev_pitch)] = best_move
        return best_score 
    
    # Solve
    state = (bisect_left(times, start_time), None, None)
    best(*state)
    #choice contains all information that is needed to remove notes from the score
    #now, we remove all notes that we chose
 
    # Reconstruct by walking the stored decisions forward
    frame = stream.Stream()
    #while the state has a successor
    while state in choice:
        next_idx, part, pitch, note = choice[state]
 
        if note is not None:
            frame.insert(times[state[0]] - start_time, note)
        state = (next_idx, part, pitch)
    
    return frame,choice
build_frame(originalScore,0,300,getScoresDict(originalScore,100))[0].show()


def rearrangePiece(score, numParts,length):
    newScore=stream.Score()
    for i in range(numParts):
        scoresDict=getScoresDict(score,2)
        frame,choices=build_frame(score,0,length,scoresDict)
        for state in choices.values():
            next_idx, part, pitch, note = state
            #remove that note from the score. 
            if note:
               print("success")
               score.parts[part].remove(note)
        newScore.append(frame)
    return newScore

rearrangePiece(originalScore,3,100).show()

        
            
         
       



 
    
 


        
        




