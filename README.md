# AI-Chamber-Music-Reduction-
Many classical composers write pieces for a specific ensemble. For example, Beethoven wrote his symphonies for a mid-sized orchestra. Many composers and musicologists have spent lots of times trying to rearrange these pieces for a different ensemble (turning Beethoven Symphony into a string quartet). This project aims to do this algorithmically.

The importance of certain notes in a piece of music can be described using Shannon entropy:

$$
H(X) = -\sum_{i=1}^{n} p(x_i)\log_2 p(x_i)
$$

This measures the amount of variation within a musical line. Musical lines with greater variation may contain more information and are potentially more important.

We describe Shannon entropy in two different ways:

1. Pitch Entropy

The entropy of the different pitches within a bar, calculated by summing the probabilities of each pitch multiplied by the logarithm of its probability:

$$
H_{\text{pitch}} = -\sum_{p \in P} P(p)\log_2 P(p)
$$

where (P(p)) is the proportion of notes in the bar that have pitch (p).

2. Inter-Onset Interval Entropy

The entropy of the inter-onset intervals (IOIs), which represent the time between consecutive note attacks.

First, we calculate each inter-onset interval:

$$
IOI_i = t_i - t_{i-1}
$$

where (t_i) is the onset time of the current note and (t_{i-1}) is the onset time of the previous note.

We then calculate the entropy of the resulting intervals:

$$
H_{\text{IOI}} = -\sum_{d \in D} P(d)\log_2 P(d)
$$

where (D) is the set of distinct inter-onset intervals and (P(d)) is the proportion of intervals equal to (d).
