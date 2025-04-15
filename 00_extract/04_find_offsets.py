import argparse
import collections
import glob
import json
import re
import tqdm

import scc_lib

parser = argparse.ArgumentParser(description="")
parser.add_argument("-d", "--data_dir", default="", type=str, help="")
parser.add_argument("-c",
                    "--conference",
                    type=str,
                    choices=scc_lib.Conference.ALL,
                    help="conference_year, e.g. iclr_2022",
                    required=True)

SectionOffset = collections.namedtuple("SectionOffset",
    "sentence_offset token_offset title".split())


def calculate_section_offsets(filename):
    output_filename = filename.replace("diffs.json", "section_offsets.json")
    with open(filename, 'r') as f:
        try:
            obj = json.load(f)
        except json.decoder.JSONDecodeError:
            return

        tokens = obj['tokens']['source']
        offsets = []
        current_section = 0

        for sentence_i, sentence in enumerate(tokens):
            if (len(sentence) > 1
                and re.match("^[0-9]+$", sentence[0])
                and re.match('^[A-Z]+$', sentence[1])
                and int(sentence[0]) == current_section + 1
                ):
                title = None
                print(sentence)
                for token_i, token in enumerate(sentence[1:]):
                    if not re.match('^[A-Z]+$', token):
                        title = sentence[1:token_i+1]
                        break
                if title is None:
                    title = sentence[1:]

                offsets.append(SectionOffset(
                    sentence_i,
                    len(sum(tokens[:sentence_i], [])),
                    title
                    )._asdict())
                current_section += 1

        for x in offsets:
            print(x)
        print()
        print("*" * 80)


def main():

    args = parser.parse_args()

    for diff_filename in tqdm.tqdm(
            list(glob.glob(
                f"{args.data_dir}/{args.conference}/*/diffs.json"))[:100]):
        calculate_section_offsets(diff_filename)


if __name__ == "__main__":
  main()

