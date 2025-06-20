import argparse
import csv
import glob
import json
import tqdm

import new_scc_lib

parser = argparse.ArgumentParser(description="")
parser.add_argument("-d", "--data_dir", default="", type=str, help="")


def main():
    args = parser.parse_args()
    records = []
    for conference in new_scc_lib.Conference.ALL:
        for initial_filename in tqdm.tqdm(
            list(glob.glob(
                f"{args.data_dir}/{conference}/*/metadata.json"))):

            with open(initial_filename, 'r') as f:
                obj = json.load(f)
                info = {"forum_id": obj["identifier"],
                        "conference": conference}
                info.update(obj['urls'])
                records.append(info)
    with open('debug_info.tsv', 'w') as f:
        writer = csv.DictWriter(f, delimiter="\t",
            fieldnames="forum_id conference initial final forum".split())
        writer.writeheader()
        for r in records:
            writer.writerow(r)

if __name__ == "__main__":
  main()

