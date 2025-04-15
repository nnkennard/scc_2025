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

Section = collections.namedtuple(
    "Section", "token_start token_excl_end title_tokens persuasive".split())

ALL_CAPS_WORD = re.compile('^[A-Z]+$')
SEC_NUMBER_INTEGER = re.compile('^[0-9]+$')
CAPITALIZED_WORD = re.compile('^[A-Z][a-z]+$')


def calculate_section_offsets(filename):
    output_filename = filename.replace("diffs.json", "section_offsets.json")
    with open(filename, 'r') as f:
        try:
            obj = json.load(f)
        except json.decoder.JSONDecodeError:
            return

    flat_tokens = sum(obj['tokens']['source'], [])

    sec_num = 0
    section_builders = [(flat_tokens.index('ABSTRACT'), ['ABSTRACT'], True)]
    for i, token in enumerate(flat_tokens[:-1]):
        if (re.match(SEC_NUMBER_INTEGER, token)
                and re.match(ALL_CAPS_WORD, flat_tokens[i + 1])
                and int(token) == sec_num + 1):
            # Maybe the next section. Check before confirming
            is_section = True
            title_tokens = []
            for j in range(i + 1, len(flat_tokens)):
                t = flat_tokens[j]
                if re.match(ALL_CAPS_WORD, t):  # More title words
                    title_tokens.append(t)
                    continue
                elif re.match('^[A-Z][a-z]+$', t):  # First non-title word
                    break
                elif (t == token  # Starting subsection
                      and
                      flat_tokens[j + 1] == "."  # e.g. "4" followed by "4.1"
                      and flat_tokens[j + 2] == "1"):
                    break
                else:
                    is_section = False  # Something else, e.g. a table
                    break
            if is_section:
                if (title_tokens == ["INTRODUCTION"]
                        or title_tokens == ["CONCLUSION"]
                        or title_tokens == ["DISCUSSION"]):
                    persuasive = True
                else:
                    persuasive = False
                section_builders.append((i, title_tokens, persuasive))
                sec_num += 1

    section_builders.append(
        (len(flat_tokens), [], None))  # Placeholder section

    sections = []
    for this_section, next_section in zip(section_builders[:-1],
                                          section_builders[1:]):
        token_start, title_tokens, persuasive = this_section
        token_excl_end = next_section[0]
        sections.append(
            Section(token_start, token_excl_end, title_tokens, persuasive))

    with open(output_filename, 'w') as f:
        f.write(json.dumps(sections, indent=2))


def main():

    args = parser.parse_args()

    for diff_filename in tqdm.tqdm(
            list(glob.glob(f"{args.data_dir}/{args.conference}/*/diffs.json"))
        [:5]):
        calculate_section_offsets(diff_filename)


if __name__ == "__main__":
    main()
