import collections
import difflib

MATCHING_BLOCK = "MatchingBlock"
NONMATCHING_BLOCK = "NonMatchingBlock"

MatchingBlock = collections.namedtuple(MATCHING_BLOCK, "a b l".split())
NonMatchingBlock = collections.namedtuple(NONMATCHING_BLOCK,
                                            "a b l_a l_b".split())

def is_matching_block(block):
    return type(block) == type(MatchingBlock)
    #return type(block).endswith("."+MATCHING_BLOCK)

def flatten_sentences(sentences):
    return sum(sentences, [])

class Diff(object):
    def __init__(self, unflat_source_tokens, unflat_dest_tokens):
        self.source_tokens = flatten_sentences(unflat_source_tokens)
        self.dest_tokens = flatten_sentences(unflat_dest_tokens)


    def calculate(self):
        diffs = []
        self.blocks = self._get_matching_blocks()
        self._reconstruct_from_blocks()
        for block in self.blocks:
            if type(block) == "NonMatchingBlock":
                diffs += self._diff_blocks(block)


    def _get_matching_blocks(self):
        matching_blocks = difflib.SequenceMatcher(
        None, self.source_tokens, self.dest_tokens).get_matching_blocks()

        blocks = []
        first_matching_block = matching_blocks[0]

        if first_matching_block[:2] != (0, 0):
            # The pair does not start with a matching block, add a
            # NonMatchingBlock
            source_cursor, dest_cursor = first_matching_block[:2]
            blocks.append(NonMatchingBlock(0, 0, source_cursor, dest_cursor))

        for left, right in zip(matching_blocks[:-1], matching_blocks[1:]):
            blocks.append(MatchingBlock(*left))
            source_cursor = left.a + left.size
            dest_cursor = left.b + left.size
            source_nonmatching_len = right.a - source_cursor
            dest_nonmatching_len = right.b - dest_cursor
            blocks.append(
                NonMatchingBlock(source_cursor, dest_cursor,
                source_nonmatching_len, dest_nonmatching_len))

        return blocks

    def _reconstruct_from_blocks(self):
        reconstructed_tokens = []
        for block in self.blocks:
            if isinstance(block, MatchingBlock):
                reconstructed_tokens += self.source_tokens[
                    block.a:block.a+block.l]
            else:
                assert isinstance(block, NonMatchingBlock)
                if block.l_b:
                    reconstructed_tokens += self.dest_tokens[
                        block.b:block.b+block.l_b]

        assert reconstructed_tokens == self.dest_tokens

    def _diff_blocks(self, block):
        pass
def make_diffs(unflat_source_tokens, unflat_dest_tokens):

    new_diff = Diff(unflat_source_tokens, unflat_dest_tokens)
    new_diff.calculate()


