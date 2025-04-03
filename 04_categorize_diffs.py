import argparse
import glob
import json
import tqdm

parser = argparse.ArgumentParser(description="")
parser.add_argument("-d", "--data_dir", default="", type=str, help="")

SMALL_DIFF_LENS = [
    (0, 1),  # One token added
    (1, 0),  # One token deleted
    (1, 1)  # One token changed
]


def process_diffs(obj):
    for diffs in obj['diffs']:
        diff_len = (len(diffs['old']), len(diffs['new']))
        print(diff_len)


def main():
    args = parser.parse_args()
    for filename in tqdm.tqdm(list(
            glob.glob(f"{args.data_dir}/*/diffs.json"))):
        with open(filename, 'r') as f:
            obj = json.load(f)
            processed_diffs = process_diffs(obj)


if __name__ == "__main__":
    main()
