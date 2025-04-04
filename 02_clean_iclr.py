"""Edit out recurring boilerplate in OpenReview files to reduce noise in diffs.

Also, leave out references (for now)
"""

import argparse
import glob
import json
import sys
import re
import tqdm

import scc_lib

parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "-d",
    "--data_dir",
    default="forums/",
    type=str,
    help="Data dir",
)
parser.add_argument("-c",
                    "--conference",
                    type=str,
                    choices=scc_lib.Conference.ALL,
                    help="conference_year, e.g. iclr_2022",
                    required=True)


UNDER_REVIEW_RE = re.compile(
    "Under review as a conference paper at ICLR 20[0-9]{2}")
#Under review as a conference paper at ICLR 2022
PUBLISHED_RE = re.compile("Published as a conference paper at ICLR 20[0-9]{2}")
REFERENCE_START = re.compile("^R\s?EFERENCES")

ABSTRACT = "ABSTRACT"
REFERENCES = "REFERENCES"

#TODO: find out what ABSTRACT_HEADER and SECTION_HEADER as supposed to do


def clean_file(filename):

    with open(filename, 'r') as f:
        lines = [line.strip() for line in f.readlines()]

    # Figure out what the boilerplate line is. For rejected papers, the final
    # pdf may still be 'Under review'.
    for line in lines:
        if UNDER_REVIEW_RE.match(line):
            boilerplate_re = UNDER_REVIEW_RE
            break
        elif PUBLISHED_RE.match(line):
            boilerplate_re = PUBLISHED_RE
            break

    final_lines = []

    for line in lines:
        if not line:
            continue
        if line.startswith("R EFERENCES") or line.startswith(REFERENCES):
            # Typo fixed in 2022
            # References starting. We are done.
            break
        matched = False
        if boilerplate_re.match(line):
            final_lines += re.split(boilerplate_re, line)
        elif ABSTRACT in line and not line.startswith(ABSTRACT):
            before, after = re.split(ABSTRACT, line)
            final_lines += [before, ABSTRACT + after]
        else:
            final_lines.append(line)

    return "\n".join(final_lines)


def main():
    args = parser.parse_args()
    for filename in
    tqdm.tqdm(list(glob.glob(f'{args.data_dir}/{args.conference}/*/*_raw.txt'))):
        with open(filename.replace("_raw", ""), 'w') as f:
            f.write(clean_file(filename))


if __name__ == "__main__":
    main()
