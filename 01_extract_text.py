"""Extract text from OpenReview PDFs.
"""

import argparse
import glob
import os
import tqdm
import subprocess

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

PLACEHOLDER = "$$$$$$$$$$$$$"

ERROR_PREFIX = "Error: Could not find 'pdftotext'"


def extract_text(pdf_path):
    # pdfdiff with only one command line argument simply extracts pdf text.
    output = subprocess.run(["python", "pdfdiff.py", pdf_path],
                            capture_output=True).stdout
    # TODO: check for errors

    output = output.decode()
    if output.startswith(ERROR_PREFIX):
        return None

    return (output.replace(  # clean up whitespace
        "-\n",
        ""  # remove hyphenations
    ).replace(
        "\n\n",
        PLACEHOLDER  # placeholder for real newlines
    ).replace(
        "\n",
        " "  # remove line breaks
    ).replace(
        PLACEHOLDER,
        "\n\n"  # restore real newlines
    ))


def main():
    args = parser.parse_args()
    for pdf_path in tqdm.tqdm(
            list(glob.glob(f"{args.data_dir}/{args.conference}/*/*.pdf"))):
        print(pdf_path)
        output_path = pdf_path.replace('.pdf', '_raw.txt')
        if os.path.isfile(output_path):
            # PDF text has already been extracted
            continue
        else:
            with open(output_path, 'w') as f:
                text = extract_text(pdf_path)
                if text is not None:
                    f.write(text)
                else:
                    print("pdftotext error")
                    break


if __name__ == "__main__":
    main()
