import collections
import difflib
import myers
import re

MATCHING_BLOCK = "MatchingBlock"
NONMATCHING_BLOCK = "NonMatchingBlock"

MatchingBlock = collections.namedtuple(MATCHING_BLOCK, "a b l".split())
NonMatchingBlock = collections.namedtuple(NONMATCHING_BLOCK,
                                            "a b l_a l_b".split())
Diff = collections.namedtuple("Diff", "index old new".split())

def flatten_sentences(sentences):
    return sum(sentences, [])

class DocumentDiff(object):
    def __init__(self, unflat_source_tokens, unflat_dest_tokens):
        self.source_tokens = flatten_sentences(unflat_source_tokens)
        self.dest_tokens = flatten_sentences(unflat_dest_tokens)


    def calculate(self):
        diffs = []
        self.blocks = self._get_matching_blocks()
        self._reconstruct_from_blocks()
        for block in self.blocks:
            if isinstance(block, NonMatchingBlock):
                diffs += self._diff_within_block(block)

        self.diffs = diffs
        self._reconstruct_from_diffs()


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

    def _diff_within_block(self, block):
        myers_diff = myers.diff(
            self.source_tokens[block.a:block.a+block.l_a],
            self.dest_tokens[block.b:block.b+block.l_b]
        )
        diff_str = "".join(x[0] for x in myers_diff)
        diffs = []
        for m in re.finditer("[ir]+", diff_str):
            tokens_added = []
            tokens_deleted = []
            for i in range(*m.span()):
                action, token = myers_diff[i]
                if action == 'i':
                    tokens_added.append(token)
                else:
                    tokens_deleted.append(token)
            diffs.append(Diff(block.a, tokens_deleted, tokens_added))
        return diffs

    def _reconstruct_from_diffs(self):
        reconstructed_tokens = []
        source_cursor = 0
        for diff in self.diffs:
            reconstructed_tokens += self.source_tokens[source_cursor:diff.index]
            reconstructed_tokens += diff.new
            source_cursor = diff.index + len(diff.old)

        reconstructed_tokens += self.source_tokens[source_cursor:]
        assert reconstructed_tokens == self.dest_tokens


def make_diffs(unflat_source_tokens, unflat_dest_tokens):

    new_diff = DocumentDiff(unflat_source_tokens, unflat_dest_tokens)
    new_diff.calculate()
    for x in new_diff.diffs:
        print(x)


