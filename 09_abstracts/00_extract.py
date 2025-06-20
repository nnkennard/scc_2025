import argparse
import collections
import glob
#import json
import re
import tqdm

import new_scc_lib

parser = argparse.ArgumentParser(description="")
parser.add_argument("-d", "--data_dir", default="", type=str, help="")

VERSION_INFO_FIELDS = "title abstract intro debug_next_sec".split()
VersionInfo = collections.namedtuple("VersionInfo", VERSION_INFO_FIELDS)

PAPER_INFO_FIELDS = "conference forum_id initial_info final_info".split()
PaperInfo = collections.namedtuple("PaperInfo", PAPER_INFO_FIELDS)

ParseError = collections.namedtuple("ParseError",
                                    "hint forum_id version".split())


def subtitle_splitter(subtitle_strings, text):
    """Split text into before and after a subheading."""
    for subtitle in subtitle_strings:
        if subtitle in text:
            try:
                pre, post = text.split(subtitle, 1)
                return pre.strip(), post.strip()
            except ValueError:
                return None
    return None


def parse_extracted_iclr_text(filename, metadata):

    with open(filename, 'r') as f:
        text = f.read().strip()

    if not text:
        return ParseError("Empty file", *metadata)

    # Text usually starts with the title in all caps.
    # Either the title is on its own line or the authors (either named or
    # anonymous) are on the same line after the title.
    maybe_title = text.split("\n")[0]
    if 'Anonymous' in maybe_title:  # Split before 'Anonymous'
        r = re.search("Anonymous", maybe_title).span()[0]
        title = maybe_title[:r]
    else:
        maybe_name_start = re.search("[A-Z][a-z]", maybe_title)
        if maybe_name_start is not None:  # A name-looking substring occurs
            title = maybe_title[:maybe_name_start.span()[0]]
        else:
            title = maybe_title  # Title occurs on its own line?

    # Most papers have either 'Abstract' or 'ABSTRACT' pretty reliably
    try:
        pre_abs, post_abs = subtitle_splitter(["Abstract", "ABSTRACT"], text)
    except TypeError:  # Because it returned None
        # Sometimes this fails but it's rare
        return ParseError("Finding Abstract heading", *metadata)

    # Try to find the first section which should be Introduction
    try:
        abstract, post_int = subtitle_splitter(
            ["1 Introduction", "1 INTRODUCTION"], post_abs)
    except TypeError:  # Because it returned None
        # Sometimes there is text before the first section starts, or the first
        # section is called something besides introduction, like "Motivation"
        return ParseError("Finding Introduction heading", *metadata)

    # Find the start of the second section in order to delimit the
    # introduction.
    next_sec_offset = re.search("2\s[A-Z]+", post_int).span()[0]
    introduction = post_int[:next_sec_offset]
    next_sec = post_int[next_sec_offset:next_sec_offset + 50]

    return VersionInfo(title, abstract, introduction, next_sec)


def main():
    args = parser.parse_args()
    papers = []
    errors = []
    error_count = 0
    for conference in new_scc_lib.Conference.ALL:
        for initial_filename in tqdm.tqdm(
                list(
                    glob.glob(f"{args.data_dir}/{conference}/*/initial.txt"))):
            forum_id = initial_filename.split("/")[-2]
            initial_info = parse_extracted_iclr_text(
                initial_filename, (forum_id, new_scc_lib.INITIAL))
            final_info = parse_extracted_iclr_text(
                initial_filename.replace('initial', 'final'),
                (forum_id, new_scc_lib.FINAL))

            if isinstance(initial_info, VersionInfo) and isinstance(
                    final_info, VersionInfo):
                papers.append(
                    PaperInfo(conference, forum_id, initial_info._asdict(),
                              final_info._asdict()))
            else:
                for info in [initial_info, final_info]:
                    if isinstance(info, ParseError):
                        errors.append(info)
                error_count += 1

    print(
        f'Num errors: {error_count} ({len(errors)}); Parsed papers: {len(papers)}'
    )
    new_scc_lib.namedtuples_to_jsonl(papers, 'abstract_intro_versions.jsonl')
    new_scc_lib.namedtuples_to_jsonl(errors, 'errors.jsonl')


if __name__ == "__main__":
    main()
