import argparse
import collections
import glob
import json
import re
import tqdm

import scc_lib

parser = argparse.ArgumentParser(description="")
parser.add_argument("-d", "--data_dir", default="", type=str, help="")


def find_review_scores(metadata_filename):
    with open(metadata_filename, 'r') as f:
        obj = json.load(f)
        scores = []
        for review in obj['reviews']:
            if 'rating' in review:
                if re.match('^[0-9][0-9]?\:', review['rating']):
                    scores.append(int(review['rating'].split(':')[0]))
                else:
                    assert False
            else:
                assert False

    return obj['identifier'], scores


def main():

    args = parser.parse_args()

    score_map = collections.defaultdict(dict)

    for conference in scc_lib.Conference.ALL:
        print(conference)
        for metadata_filename in tqdm.tqdm(
                list(glob.glob(
                    f"{args.data_dir}/{conference}/*/metadata.json"))):
            forum, scores = find_review_scores(metadata_filename)
            score_map[conference][forum] = scores

    with open('review_scores.json', 'w') as f:
        f.write(json.dumps(score_map, indent=2))


if __name__ == "__main__":
    main()
