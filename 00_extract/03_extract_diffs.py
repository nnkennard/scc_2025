import argparse
import glob
import json
import os
import tqdm

import scc_lib
from scc_diff_lib import DocumentDiff

parser = argparse.ArgumentParser(description="")
parser.add_argument("-d", "--data_dir", default="", type=str, help="")
parser.add_argument("-c",
                    "--conference",
                    type=str,
                    choices=scc_lib.Conference.ALL,
                    help="conference_year, e.g. iclr_2022",
                    required=True)


def generate_filenames(initial_text_file):
    assert initial_text_file.endswith('initial.txt')
    forum = initial_text_file.split("/")[-2]
    return (f'{initial_text_file[:-11]}final.txt',
            f'{initial_text_file[:-11]}diffs.json', forum)


def read_sentencized(filename):
    with open(filename, "r") as f:
        return [line.split() for line in f.readlines()]


def get_tokens(filename):
    #print("tokenizing")
    with open(filename, 'r') as f:
        text = f.read()
        return list([t.to_dict()[0]['text'] for t in s.tokens]
                    for s in scc_lib.SENTENCIZE_PIPELINE(text).sentences)


def main():
    args = parser.parse_args()
    for initial_filename in tqdm.tqdm(
            list(glob.glob(
                f"{args.data_dir}/{args.conference}/*/initial.txt"))):

        final_filename, diff_file, forum = generate_filenames(initial_filename)

        if not os.path.isfile(diff_file):
            d = DocumentDiff(get_tokens(initial_filename),
                             get_tokens(final_filename), forum)
            with open(diff_file, 'w') as f:
                f.write(d.dump())


if __name__ == "__main__":
    main()
