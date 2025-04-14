import argparse
import collections
import glob
import json
import tqdm

from nltk.metrics.distance import edit_distance

parser = argparse.ArgumentParser(description="")
parser.add_argument("-d", "--data_dir", default="", type=str, help="")

SMALL_DIFF_LENS = [
    (1, 2),  # One token added
    (1, 0),  # One token deleted
    (1, 1)  # One token changed
]

TYPO_EDIT_DISTANCE = 4
SENTENCE_EDIT_LIMIT = 10
XL_EDIT_LIMIT = 1000


class DiffSize(object):
    TYPO = "typo"
    SMALL = "token"
    MEDIUM = "medium"
    LARGE = "large"
    XLARGE = "xlarge"


def process_diffs(obj):
    sizes = collections.Counter()
    for diff in obj['diffs']:
        diff_len = (len(diff['old']), len(diff['new']))
        if diff_len in SMALL_DIFF_LENS:
            a = " ".join(diff['old'])
            b = " ".join(diff['new'])
            if edit_distance(a, b) < TYPO_EDIT_DISTANCE:
                sizes[DiffSize.TYPO] += 1
            else:
                sizes[DiffSize.SMALL] += 1
        elif max(diff_len) < SENTENCE_EDIT_LIMIT:
            a = " ".join(diff['old'])
            b = " ".join(diff['new'])
            if edit_distance(a, b) < TYPO_EDIT_DISTANCE:
                sizes[DiffSize.TYPO] += 1
            else:
                sizes[DiffSize.MEDIUM] += 1
                print(diff)
        elif max(diff_len) > XL_EDIT_LIMIT:
            sizes[DiffSize.XLARGE] += 1
        else:
            sizes[DiffSize.LARGE] += 1
    return sizes


def main():
    args = parser.parse_args()

    size_totals = collections.Counter()
    for filename in tqdm.tqdm(list(
            glob.glob(f"{args.data_dir}/*/*/diffs.json"))):
        with open(filename, 'r') as f:
            try:
                obj = json.load(f)
                size_totals.update(process_diffs(obj))
            except ValueError:
                pass

    for k, v in size_totals.items():
        print(k, v)

if __name__ == "__main__":
    main()
