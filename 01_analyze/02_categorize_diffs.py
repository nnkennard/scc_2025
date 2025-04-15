import argparse
import collections
import glob
import json
import os
import tqdm

import scc_lib
from nltk.metrics.distance import edit_distance

parser = argparse.ArgumentParser(description="")
parser.add_argument("-d", "--data_dir", default="", type=str, help="")
parser.add_argument("-c",
                    "--conference",
                    type=str,
                    choices=scc_lib.Conference.ALL,
                    help="conference_year, e.g. iclr_2022",
                    required=True)


SMALL_DIFF_LENS = [
    (1, 2),  # One token added
    (1, 0),  # One token deleted
    (1, 1)  # One token changed
]
TYPO_EDIT_DISTANCE = 4
XL_LIMIT = 1000


class DiffClass(object):
    NONALPHA = "nonalpha"
    TYPO = "typo"
    XLARGE = "xlarge"
    ALL = [NONALPHA, TYPO, XLARGE]


class DiffSize(object):
    TOKEN = "token"
    IN_SENTENCE = "in_sentence"
    MULTI_SENTENCE = "multi_sentence"
    ALL = [TOKEN, IN_SENTENCE, MULTI_SENTENCE]


def is_mostly_nonalpha(diff):
    chars = "".join(diff["old"] + diff["new"])
    alpha_chars = [x for x in chars if x.isalpha()]
    return len(alpha_chars) < len(chars) / 2


def write_to_file(handle, diff, forum):
    d = {'forum': forum}
    d.update(diff)
    handle.write(json.dumps(d) + "\n")


def compute_sentence_ranges(obj):
    tokens_seen = 0
    sentence_ranges = []
    for sentence in obj['tokens']['source']:
        end = tokens_seen + len(sentence)
        sentence_ranges.append(range(tokens_seen, end))
        tokens_seen = end

    return sentence_ranges


def is_in_sentence(diff, sentence_ranges):
    for r in sentence_ranges:
        if diff['index'] in r:
            if diff['index'] + len(diff['old']) in r:
                return True
            else:
                return False
    assert False


def process_diffs(obj, forum, file_handles):
    diffs = collections.defaultdict(list)

    references_index = sum(obj['tokens']['source'], []).index('REFERENCES')

    sentence_ranges = compute_sentence_ranges(obj)

    for diff in obj['diffs']:

        if diff['index'] > references_index:
            continue

        diff_category = None
        if is_mostly_nonalpha(diff):
            diff_category = DiffClass.NONALPHA
        else:
            diff_len = (len(diff['old']), len(diff['new']))
            if max(diff_len) > XL_LIMIT:
                diff_category = DiffClass.XLARGE
            elif is_in_sentence(diff, sentence_ranges):
                a = " ".join(diff['old'])
                b = " ".join(diff['new'])
                if edit_distance(a, b) < TYPO_EDIT_DISTANCE:
                    diff_category = DiffClass.TYPO
                elif diff_len in SMALL_DIFF_LENS:
                    diff_category = DiffSize.TOKEN
                else:
                    diff_category = DiffSize.IN_SENTENCE
            else:
                diff_category = DiffSize.MULTI_SENTENCE

        assert diff_category is not None
        write_to_file(file_handles[diff_category], diff, forum)


def main():
    args = parser.parse_args()

    reduced_diffs_path = f"{args.data_dir}/{args.conference}/reduced_diffs/"
    os.makedirs(reduced_diffs_path, exist_ok=True)
    file_handles = {}
    for category in DiffSize.ALL + DiffClass.ALL:
        file_handles[category] = open(f'{reduced_diffs_path}/{category}.jsonl',
                                      'w')

    for filename in tqdm.tqdm(
            list(
                glob.glob(f"{args.data_dir}/{args.conference}/*/diffs.json"))):
        with open(filename, 'r') as f:
            try:
                forum = filename.split('/')[-2]
                obj = json.load(f)
                process_diffs(obj, forum, file_handles)
            except ValueError:
                pass

    for category, handle in file_handles.items():
        handle.close()


if __name__ == "__main__":
    main()
