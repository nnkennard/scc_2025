import argparse
import collections
import glob
import json
import os
import tqdm

import scc_lib
from nltk.metrics.distance import edit_distance

parser = argparse.ArgumentParser(description="")
parser.add_argument("-d", "--data_dir",
    default="/gypsum/work1/mccallum/nnayak/scc_2025_recorded/", type=str, help="")
parser.add_argument("-c",
                    "--conference",
                    type=str,
                    choices=scc_lib.Conference.ALL,
                    help="conference_year, e.g. iclr_2022",
                    required=True)

AugmentedDiff = collections.namedtuple("AugmentedDiff",
    "forum index old new type section persuasive".split())

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
    BOILERPLATE = "boilerplate"
    TITLE = "title"
    ALL = [NONALPHA, TYPO, XLARGE, BOILERPLATE, TITLE]


class DiffSize(object):
    TOKEN = "token"
    IN_SENTENCE = "in_sentence"
    MULTI_SENTENCE = "multi_sentence"
    ALL = [TOKEN, IN_SENTENCE, MULTI_SENTENCE]


def is_mostly_nonalpha(diff):
    chars = "".join(diff["old"] + diff["new"])
    alpha_chars = [x for x in chars if x.isalpha()]
    return len(alpha_chars) < len(chars) / 2

BOILERPLATE_TERMS = [
"Anonymous authors",
"Corresponding",
"Correspondence",
"Contribution",
"Under review as a conference paper"]

def is_boilerplate(diff):
    diff_text = " ".join(diff['old'] + diff['new'])
    if "ICLR" in diff_text:
        print(diff_text)
        print(diff)
        print()

    for t in BOILERPLATE_TERMS:
        if t in diff_text:
            return True
    return False

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


def get_diff_type(diff, sentence_ranges):
    diff_type = None
    if is_mostly_nonalpha(diff):
        diff_type = DiffClass.NONALPHA
    elif is_boilerplate(diff):
        diff_type = DiffClass.BOILERPLATE
    else:
        diff_len = (len(diff['old']), len(diff['new']))
        if max(diff_len) > XL_LIMIT:
            diff_type = DiffClass.XLARGE
        elif is_in_sentence(diff, sentence_ranges):
            a = " ".join(diff['old'])
            b = " ".join(diff['new'])
            if edit_distance(a, b) < TYPO_EDIT_DISTANCE:
                diff_type = DiffClass.TYPO
            elif diff_len in SMALL_DIFF_LENS:
                diff_type = DiffSize.TOKEN
            else:
                diff_type = DiffSize.IN_SENTENCE
        else:
            diff_type = DiffSize.MULTI_SENTENCE

    assert diff_type is not None
    return diff_type


def process_section_obj(section_file):
    range_map = {}
    with open(section_file, 'r') as f:
        obj = json.load(f)

        for (start, end, name, is_persuasive) in obj:
            range_map[range(start, end)] = (name, is_persuasive)
    return range_map

def process_diffs(obj, forum, file_handles, section_map):
    diffs = collections.defaultdict(list)

    references_index = sum(obj['tokens']['source'], []).index('REFERENCES')

    sentence_ranges = compute_sentence_ranges(obj)

    for diff in obj['diffs']:

        if diff['index'] > references_index:
            continue

        diff_type = get_diff_type(diff, sentence_ranges)

        section, is_persuasive = "None", False
        for index_range, section_info in section_map.items():
            if diff['index'] in index_range:
                section, is_persuasive = section_info
                break

        augmented_diff = AugmentedDiff(forum,
        diff['index'], diff['old'], diff['new'],
        diff_type, section, is_persuasive)
        file_handles[diff_type].write(json.dumps(augmented_diff) + "\n")


def main():
    args = parser.parse_args()

    reduced_diffs_path = f"{args.data_dir}/{args.conference}/reduced_diffs/"
    os.makedirs(reduced_diffs_path, exist_ok=True)
    print(reduced_diffs_path)
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
                section_map = process_section_obj(
                    filename.replace('diffs','section_offsets'))
                process_diffs(obj, forum, file_handles, section_map)
            except ValueError:
                pass

    for category, handle in file_handles.items():
        handle.close()


if __name__ == "__main__":
    main()
