import difflib
import myers

import diff_lib_2
import re

source_tokens = ("twas brillig and the slithy toves did gyre and gimble in the wabe"
    " all mimsy were the borogoves and the mome raths outgrabe").split()

dest_tokens = ("twasn't brillig and in uffish thought the slithy toves did gyre in the"
    " wabe all mimsy were the borogoves and the mome raths outgrabe").split()

"""
(testName) gypsum-gpu096 scc_2025 $ python blerp.py
rikkiiikkkkkrrkkkkkkkkkkkkk
<re.Match object; span=(0, 2), match='ri'>
<re.Match object; span=(4, 7), match='iii'>
<re.Match object; span=(12, 14), match='rr'>
"""

diff_lib_2.make_diffs([source_tokens], [dest_tokens])

