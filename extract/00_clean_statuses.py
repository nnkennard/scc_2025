import argparse
import collections
import csv
import openreview

import scc_lib

parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "-d",
    "--data_dir",
    default="forums/",
    type=str,
    help="Data dir",
)
parser.add_argument(
    "-s",
    "--status_dir",
    default="statuses/",
    type=str,
    help="Status dir",
)

VALID_DECISIONS = [
    "Accept: notable-top-25%", "Accept: notable-top-5%", "Accept (Oral)",
    "Accept: poster", "Accept (Poster)", "Accept (Spotlight)", "Accept (Talk)",
    "Invite to Workshop Track", "No judgement (proceed with normal process)",
    "None", "Reject"
]

GUEST_CLIENT = openreview.Client(baseurl='https://api.openreview.net')


def find_actual_decision(forum, conference, bad_decision):
    assert conference in [
        scc_lib.Conference.iclr_2022, scc_lib.Conference.iclr_2023
    ]
    return "None"
    dec = None
    for note in GUEST_CLIENT.get_notes(forum=forum):
        if 'Decision' in note.invitation:
            dec = note.content['decision']
            break
    assert dec is not None
    return dec


def main():
    args = parser.parse_args()
    counts = collections.Counter()
    final_lines = []
    for conference in scc_lib.Conference.ALL:
        with open(f'{args.status_dir}/status_{conference}.tsv', 'r') as f:
            reader = csv.DictReader((x.replace('\0', '') for x in f),
                                    delimiter='\t')
            for row in reader:
                counts[(row["#Conference"], row["Status"],
                        row["Decision"])] += 1
                if row['Decision'] not in VALID_DECISIONS:
                    new_row = dict(row)
                    new_row["Decision"] = find_actual_decision(
                        row['Forum'], row['#Conference'], row['Decision'])
                    final_lines.append(new_row)
                else:
                    final_lines.append(row)

    with open('statuses.tsv', 'w') as f:
        writer = csv.DictWriter(
            f,
            fieldnames="#Conference Forum Status Decision".split(),
            delimiter='\t')
        writer.writeheader()
        for row in final_lines:
            writer.writerow(row)


if __name__ == "__main__":
    main()
