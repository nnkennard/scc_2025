"""Extract text from OpenReview PDFs.
"""

import argparse
import glob
import os
import tqdm
import subprocess

parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "-d",
    "--data_dir",
    default="forums/",
    type=str,
    help="Data dir",
)

PLACEHOLDER = "$$$$$$$$$$$$$"


def extract_text(pdf_path):
    # pdfdiff with only one command line argument simply extracts pdf text.
    output = subprocess.run(["python", "pdfdiff.py", pdf_path],
                            capture_output=True).stdout
    # TODO: check for errors

    return (output.decode(  # Clean up whitespace quirks
    ).replace(
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
    for pdf_path in tqdm.tqdm(list(glob.glob(f"{args.data_dir}/*/*.pdf"))):
        output_path = pdf_path.replace('.pdf', '_raw.txt')
        if os.path.isfile(output_path):
            # PDF text has already been extracted
            continue
        else:
            with open(output_path, 'w') as f:
                f.write(extract_text(pdf_path))


if __name__ == "__main__":
    main()
