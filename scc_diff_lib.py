"""Wrappers around Myers diff and difflib for use in scientific coconstruction.

Since source and destination sequence lengths (n and d respectively), can be
quite high, O(nd) runtime of Myers is prohibitively high. Also, since diffs can
be very localized, there are large unchanged subsequences.

We first use get_matching_blocks from difflib (Python library) to find maximal
unchanged subsequences. We invert this list to find non-matching blocks, then
use Myers to describe the edirs within the non-matching blocks.
"""

import collections
import difflib
import json
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
        # Saving these, but they are only used for output
        self.source_unflat = unflat_source_tokens
        self.dest_unflat = unflat_dest_tokens
        # Flattened tokens are used in the diff calculations
        self.source_tokens = flatten_sentences(unflat_source_tokens)
        self.dest_tokens = flatten_sentences(unflat_dest_tokens)

        self.calculate()

    def calculate(self):
        self.diffs = []

        # Get matching and nonmatching blocks, then verify block calculation
        self.blocks = self._get_matching_blocks()
        self._reconstruct_from_blocks()

        # Convert each nonmatching block into diffs
        for block in self.blocks:
            if isinstance(block, NonMatchingBlock):
                self.diffs += self._diff_within_block(block)

        # Verify diff calculation
        self._reconstruct_from_diffs()

    def _get_matching_blocks(self):
        """Get maximal matching blocks and calculate nonmatching blocks.
        """
        matching_blocks = difflib.SequenceMatcher(
            None, self.source_tokens, self.dest_tokens).get_matching_blocks()

        blocks = [] # Alternating matching and nonmatching blocks

        # Special treatment for first block
        first_matching_block = matching_blocks[0]

        if first_matching_block[:2] != (0, 0):
            # The pair does not start with a matching block, add a
            # NonMatchingBlock
            source_cursor, dest_cursor = first_matching_block[:2]
            blocks.append(NonMatchingBlock(0, 0, source_cursor, dest_cursor))

        for prev, curr in zip(matching_blocks[:-1], matching_blocks[1:]):
            # Just add in the matching block
            blocks.append(MatchingBlock(*prev))

            # Find the edges of the nonmatching block.
            # Where the previous matching block ends
            source_cursor = prev.a + prev.size
            dest_cursor = prev.b + prev.size
            # Where the next matching block starts
            source_nonmatching_len = curr.a - source_cursor
            dest_nonmatching_len = curr.b - dest_cursor
            blocks.append(
                NonMatchingBlock(source_cursor, dest_cursor,
                                 source_nonmatching_len, dest_nonmatching_len))

        return blocks

    def _diff_within_block(self, block):
        """Convert nonmatching block into a diff."""

        myers_diff = myers.diff(
            self.source_tokens[block.a:block.a + block.l_a],
            self.dest_tokens[block.b:block.b + block.l_b])

        # Convert the actions in the myers diff into a string so that regex can
        # be used
        diff_str = "".join(x[0] for x in myers_diff)

        diffs = []
        for m in re.finditer("[ir]+", diff_str):
            # A sequence of inserts and removes
            inserted = []
            removed = []
            for i in range(*m.span()):
                action, token = myers_diff[i]
                if action == 'i':
                    inserted.append(token)
                else:
                    removed.append(token)
            diffs.append(Diff(block.a, removed, inserted))
        return diffs

    def dump(self):
        return json.dumps(
            {
                "tokens": {
                    "source": self.source_unflat,
                    "dest": self.dest_unflat
                },
                "diffs": [d._asdict() for d in self.diffs]
            },
            indent=2)

    # ======= Reconstruction methods below ====================================
    # These methods are used to check for bugs in the diff logic.

    def _reconstruct_from_blocks(self):
        reconstructed_tokens = []
        for block in self.blocks:
            if isinstance(block, MatchingBlock):
                reconstructed_tokens += self.source_tokens[block.a:block.a +
                                                           block.l]
            else:
                assert isinstance(block, NonMatchingBlock)
                if block.l_b:
                    reconstructed_tokens += self.dest_tokens[block.b:block.b +
                                                             block.l_b]

        assert reconstructed_tokens == self.dest_tokens

    def _reconstruct_from_diffs(self):
        reconstructed_tokens = []
        source_cursor = 0
        for diff in self.diffs:
            reconstructed_tokens += self.source_tokens[source_cursor:diff.
                                                       index]
            reconstructed_tokens += diff.new
            source_cursor = diff.index + len(diff.old)

        reconstructed_tokens += self.source_tokens[source_cursor:]
        assert reconstructed_tokens == self.dest_tokens
