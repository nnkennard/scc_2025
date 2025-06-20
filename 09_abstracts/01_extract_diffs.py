import json
import stanza
import tqdm

import scc_diff_lib

SENTENCIZE_PIPELINE = stanza.Pipeline("en", processors="tokenize")

def get_tokens(text):
    return list([t.to_dict()[0]['text'] for t in s.tokens]
                    for s in SENTENCIZE_PIPELINE(text).sentences)


def main():

    diffs = []
    with open('diffs.jsonl','w') as g:
        with open('abstract_intro_versions.jsonl', 'r') as f:
            for line in tqdm.tqdm(f.readlines()):
                obj = json.loads(line)
                for key in ['abstract', 'intro']:
                    d = scc_diff_lib.DocumentDiff(
                        get_tokens(obj['initial_info'][key]),
                        get_tokens(obj['final_info'][key]),
                        f"{get_tokens(obj['forum_id'])}_{key}")
                    g.write(d.dump())

if __name__ == "__main__":
  main()

