import argparse
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


def process_diffs(obj):
    for diff in obj['diffs']:
        diff_len = (len(diff['old']), len(diff['new']))
        if diff_len in SMALL_DIFF_LENS:
            a = " ".join(diff['old'])
            b = " ".join(diff['new'])
            print(edit_distance(a, b), diff)


def main():
    args = parser.parse_args()
    for filename in tqdm.tqdm(list(
            glob.glob(f"{args.data_dir}/*/*/diffs.json"))):
        with open(filename, 'r') as f:
            try:
                obj = json.load(f)
                processed_diffs = process_diffs(obj)
            except ValueError:
                pass


if __name__ == "__main__":
    main()
