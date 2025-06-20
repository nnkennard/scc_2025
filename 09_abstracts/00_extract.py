import argparse
import collections
import glob
import json
import os
import re
import tqdm

import new_scc_lib

parser = argparse.ArgumentParser(description="")
parser.add_argument("-d", "--data_dir", default="", type=str, help="")
parser.add_argument("-c",
                    "--conference",
                    type=str,
                    choices=new_scc_lib.Conference.ALL,
                    help="conference_year, e.g. iclr_2022",
                    required=True)

#MINI_PARSE_RE = re.compile(("(?P<title>.*).*ABSTRACT "
#                            "(?P<abstract>.*)1\sINTRODUCTION "
#                            "(?P<intro>.+?)2\s(?P<sec2>[^a-z]+)[A-Z]"))

PAPER_INFO_FIELDS = "forum_id version title abstract intro sec2".split()

PaperInfo = collections.namedtuple("PaperInfo", PAPER_INFO_FIELDS)

def default_initial(initial_text, forum_id):
    title = initial_text.split("\n")[0]
    if 'Anonymous' in title:
        r = re.search("Anonymous", title).span()[0]
        title = title[:r]
    initial_text = initial_text.replace("\n", "").strip()
    if not initial_text:
        print(f'{forum_id}\tEmpty file')
        return None
    try:
        pre_abs, post_abs = initial_text.split("ABSTRACT", 1)
    except ValueError:
        try:
            pre_abs, post_abs = initial_text.split("Abstract", 1)
        except ValueError:
            print(f'{forum_id}\tMaybe no abstract')
            return None
    try:
        maybe_abs, post_int = post_abs.split("1 INTRODUCTION", 1)
    except ValueError:
        try:
            maybe_abs, post_int = post_abs.split("1 Introduction", 1)
        except ValueError:
            print(f'{forum_id}\tMaybe no introduction')
            return None
    r = re.search("2\s[A-Z]+", post_int).span()[0]
    maybe_int = post_int[:r]
    return PaperInfo(forum_id, new_scc_lib.INITIAL,
    title, maybe_abs, maybe_int, post_int[r:r+100])



def main():
    args = parser.parse_args()
    papers = []
    for initial_filename in tqdm.tqdm(
            list(glob.glob(
                f"{args.data_dir}/{args.conference}/*/initial.txt"))):
        forum_id = initial_filename.split("/")[-2]
        with open(initial_filename, 'r') as f:
            papers.append(default_initial(f.read().strip(),
            forum_id))

if __name__ == "__main__":
    main()
