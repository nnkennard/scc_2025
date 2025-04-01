import difflib

import diff_lib_2

source_tokens = ("twas brillig and the slithy toves did gyre and gimble in the wabe"
    " all mimsy were the borogoves and the mome raths outgrabe").split()

dest_tokens = ("twasn't brillig and in uffish thought the slithy toves did gyre in the"
    " wabe all mimsy were the borogoves and the mome raths outgrabe").split()

diff_lib_2.make_diffs([source_tokens], [dest_tokens])

#matching_blocks = difflib.SequenceMatcher(
#None, source_tokens, dest_tokens).get_matching_blocks()
#for m in matching_blocks:
#    print(m)

#print("\n".join(source_tokens))
#print("\n".join(dest_tokens))
