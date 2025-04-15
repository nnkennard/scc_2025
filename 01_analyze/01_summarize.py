import argparse
import collections
import csv
import glob
import os

import scc_lib

ACCEPT_DECISIONS = [
"Accept: notable-top-25%", "Accept: notable-top-5%", "Accept (Oral)", "Accept: poster", "Accept (Poster)", "Accept (Spotlight)", "Accept (Talk)"
]

parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "-d",
    "--data_dir",
    default="forums/",
    type=str,
    help="Data dir",
)

class Invalid(object):
    NO_PDF = "no_pdf"
    NO_REVIEWS = "no_reviews"
    NO_DECISION = "no_decision"
    PARSE_ERROR = "parse_error"
    MISSING_DECISION = "missing_decision"

class Decision(object):
    ACCEPTED = "accepted"
    NOT_ACCEPTED = "not_accepted"
    INVALID = "invalid"

class Revisions(object):
    REVISED = "revised"
    NOT_REVISED = "not_revised"

def clean_decision(decision):
    if decision in ACCEPT_DECISIONS:
        return Decision.ACCEPTED
    else:
        return Decision.NOT_ACCEPTED

def main():

    args = parser.parse_args()

    status_counter = collections.defaultdict(list)


    for conference in scc_lib.Conference.ALL:
        recorded_info = {}
        with open('statuses.tsv', 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                if not row["#Conference"] == conference:
                    continue
                recorded_info[row["Forum"]] = (row["Status"], row["Decision"])
        dir_info = {}
        for dirname in glob.glob(f'{args.data_dir}/{conference}/*/'):
            forum = dirname.split("/")[-2]
            dir_status = None
            maybe_diff_file = f'{dirname}/diffs.json'
            if os.path.isfile(maybe_diff_file):
                with open(maybe_diff_file, 'r') as f:
                    obj = f.read()
                    if obj:
                        dir_status = "complete"
                    else:
                        dir_status = "diff_error"
            else:
                dir_status = "no_diffs"
            dir_info[forum] = dir_status


        for forum, (recorded_status, decision) in recorded_info.items():
            if forum in dir_info:
                dir_status = dir_info[forum]
                if dir_status in ["diff_error", "no_diffs"]:
                    status_counter[(conference, Decision.INVALID,
                    dir_status)].append(forum)
                else:
                    assert dir_status == "complete"
                    assert recorded_status == "complete"
                    status_counter[(conference, clean_decision(decision),
                    Revisions.REVISED)].append(forum)
            else:
                if recorded_status in ["no_reviews", "no_decision", "no_pdf"]:
                    status_counter[(conference, Decision.INVALID,
                    recorded_status)].append(forum)
                else:
                    assert recorded_status == "no_revision"
                    status_counter[(conference, clean_decision(decision),
                    recorded_status)].append(forum)

        for forum in set(dir_info.keys()) - recorded_info.keys():
            status_counter[(conference, Decision.INVALID,
            Invalid.MISSING_DECISION)].append(forum)


    with open('final_statuses.tsv', 'w') as f:
        writer = csv.DictWriter(f,
        fieldnames="forum conference decision revision".split(), delimiter="\t")
        writer.writeheader()
        for (c, d, r), forums in status_counter.items():
            for forum in forums:
                writer.writerow({
                "forum": forum,
                "conference": c,
                "decision": d,
                "revision": r})


if __name__ == "__main__":
  main()

