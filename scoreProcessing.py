from music21 import *
import copy
def getAllParts(originalScore):
    """extracts only the musical parts from a score"""
    #modifies originalScore returns nothing
    for line in originalScore:
        if type(line)!=stream.Part:
            originalScore.remove(line)

 
def removeUnpitched(score):
    """
    Remove unpitched elements (e.g. percussion notated with
    music21.note.Unpitched) from every part in a Score, in place.

    """
    #ideally percussion parts should only be assigned to percurssion instruments
    #if there is percussion in a chamber group
  
    for part in score.parts:
        for measure in part.getElementsByClass('Measure'):
            unpitched_elements = list(measure.getElementsByClass('Unpitched'))
            for el in unpitched_elements:
                measure.remove(el)

def flattenVoices(score):
    new_parts = []
    for part in list(score.parts):
        measures = part.getElementsByClass(stream.Measure)
        n = max((len(m.voices) for m in measures), default=0)

        if n < 2:
            new_parts.append(part)      # reuse the original object
            continue

        for k in range(n):
            p = copy.deepcopy(part)
            for m in p.getElementsByClass(stream.Measure):
                voices = list(m.voices)
                keep = voices[k] if k <len(voices) else None
                for v in voices:
                    m.remove(v)
                if keep is not None:
                    for el in keep:
                        m.insert(el.offset, el)
            new_parts.append(p)

    for part in list(score.parts):
        score.remove(part)
    for p in new_parts:
        score.insert(0, p)

def transpose_transposing_instruments(score, to_concert=True ):
    """Convert transposing parts between written and concert (sounding) pitch.

    to_concert=True:  written -> concert pitch (e.g. Bb clarinet sounds a M2 lower)
    to_concert=False: concert -> written pitch
    """
     
    for part in score.parts:
        inst = part.getInstrument(returnDefault=False)
        if inst is None or inst.transposition is None:
            continue  # non-transposing or unknown instrument

        # Avoid transposing twice. 'unknown' is treated as "still written".
        already_concert = (part.atSoundingPitch is True)
        if to_concert == already_concert:
            continue

        # inst.transposition is the interval from written pitch to sounding pitch
        interval_to_apply = (inst.transposition if to_concert
                             else inst.transposition.reverse())
        part.transpose(interval_to_apply, inPlace=True)
        part.atSoundingPitch = to_concert

   

def createNewScore(newInstruments):
    """given list of music21 instrument classes, return a new
    score meant for these"""
    newScore = stream.Score()
    for instrument_class in newInstruments:
        # Instantiate the instrument
        instr = instrument_class()

        # Create a new part and label it
        part = stream.Part()
        part.id = instr.instrumentName          # e.g. "Clarinet"
        part.partName = instr.instrumentName     # shows up in notation/playback
        part.partAbbreviation = instr.instrumentAbbreviation 

        # Insert the instrument object at the start of the part (offset 0)hyg
        # This is what actually tells music21 (and any MusicXML export)
        # which instrument this part is for
        part.insert(0, instr)

        newScore.append(part)
    return newScore

def strip_ornaments_from_part(part: stream.Part) -> stream.Part:
    """Remove grace notes, ornaments (trills, turns, mordents, tremolos...)
    and trill/tremolo spanners from a whole part, in place."""

    # 1. Grace notes (collect first, then remove, to avoid mutating while iterating)
    graces = [n for n in part.recurse().notes if n.duration.isGrace]
    for g in graces:
        part.remove(g, recurse=True)

    # 2. Ornament expressions attached to notes/chords
    for n in part.recurse().notes:
        n.expressions[:] = [e for e in n.expressions
                            if not isinstance(e, expressions.Ornament)]

    # 3. Spanners (trill extension lines, multi-note tremolos).
    #    These live at the Part level, so this is where the part-wide version helps.
    spanner_types = (expressions.TrillExtension, expressions.TremoloSpanner)
    for sp in list(part.recurse().getElementsByClass(spanner_types)):
        part.remove(sp, recurse=True)

    return part  # modified in place; returned for convenience