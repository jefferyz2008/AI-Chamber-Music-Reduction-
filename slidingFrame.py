from music21 import*
import copy


def getFrame(part, length, center):
    #length is only half of the total bar length
    """returns a frame, centered at center quarter notes after the beginning of each part
    streching length quarter notes in both directions
    or until it reaches beginning or end."""
    start = max(0.0, center - length)                 # clamp at the beginning
    end = min(float(part.highestTime), center + length)
    assert(end-start<=8)

    frame=(part.flatten()
                .getElementsByOffset(start, end,
                                     includeEndBoundary=True,
                                     mustBeginInSpan=True)
                .stream())
    
    frame=copy.deepcopy(frame)
    for element in frame:
        element.offset -= start
 
    return frame

def getWeight(note, frame):
    """Weight of a note for sliding frame evaluation 
    1 at the center, falling linearly to 0 at `length` quarter notes away.
    center and length are the same values passed to getFrame."""
    
    offset = frame.elementOffset(note)        # onset relative to the part's start
    length=frame.duration.quarterLength
    center=length/2
    distance = abs(offset - center) 
    weight=max(0,1 - distance / length)
  
    return weight



#calculate the entropy of the whole frame, focusing on the center note,
#and applying a weight to each of the other notes not in the center 




