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


VERSION_INFO_FIELDS = "title abstract intro sec2".split()

VersionInfo = collections.namedtuple("VersionInfo", VERSION_INFO_FIELDS)

def parse_initial(initial_text, forum_id):
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
    return VersionInfo(title, maybe_abs, maybe_int, post_int[r:r+100])


def subtitle_splitter(subtitle_strings, text):
    for subtitle in substitle_strings:
        if subtitle in text:
            try:
               pre, post = text.split(subtitle, 1)
               return pre, post
            except ValueError:
                print(f"Cannot find {subtitle}")
                return None
    return None


def parse_final(final_text, forum_id):
    final_text = final_text.strip()
    title = final_text.split("\n")[0]
    if 'Anonymous' in title:
        r = re.search("Anonymous", title).span()[0]
        title = title[:r]
    else:
        maybe_name_start = re.search("[A-Z][a-z]", title)
        if maybe_name_start is not None:
            title = title[:maybe_name_start.span()[0]]
    print(title)
    final_text = final_text.replace("\n", "").strip()

    pre_abs, post_abs = subtitle_splitter(["Abstract", "ABSTRACT"], final_text)
    abstract, post_int = subtitle_splitter(["1 Introduction", "1 INTRODUCTION"],
    final_text)
    next_sec_offset = re.search("2\s[A-Z]+", post_int).span()[0]
    introduction = post_int[:r]
    return VersionInfo(title, maybe_abs, maybe_int, post_int[r:r+100])



def main():
    args = parser.parse_args()
    papers = []
    for initial_filename in tqdm.tqdm(
            list(glob.glob(
                f"{args.data_dir}/{args.conference}/*/initial.txt"))[:10]):
        forum_id = initial_filename.split("/")[-2]
        with open(initial_filename, 'r') as f:
            initial_info = parse_initial(f.read(), forum_id)
        final_filename = initial_filename.replace("initial", "final")
        with open(final_filename, 'r') as f:
            final_info = parse_final(f.read(), forum_id)
            print("=" * 80)

if __name__ == "__main__":
    main()
