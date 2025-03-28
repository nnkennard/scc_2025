"""Use OpenReview API to get initial and final PDFs for ICLR submissions.
"""


import argparse
import collections
import json
import openreview
import os
import tqdm

import scc_lib

parser = argparse.ArgumentParser(description='')
parser.add_argument('-o',
                    '--output_dir',
                    type=str,
                    help='directory to dump pdfs',
                    required=True)
parser.add_argument("-c",
                    "--conference",
                    type=str,
                    choices=scc_lib.Conference.ALL,
                    help="conference_year, e.g. iclr_2022",
                    required=True)
parser.add_argument('-s',
                    '--status_file_prefix',
                    default='./statuses/status_',
                    type=str,
                    help='prefix for tsv file with status of all forums')
parser.add_argument('-d', '--debug', action='store_true', help='')

# == OpenReview-specific stuff ===============================================


def export_signature(note):
    (signature, ) = note.signatures
    return signature.split("/")[-1]


class PDFStatus(object):
    # for paper revisions
    AVAILABLE = "available"
    DUPLICATE = "duplicate"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"


GUEST_CLIENT = openreview.Client(baseurl="https://api.openreview.net")

PDF_ERROR_STATUS_LOOKUP = {
    "ForbiddenError": PDFStatus.FORBIDDEN,
    "NotFoundError": PDFStatus.NOT_FOUND,
}

PDF_URL_PREFIX = "https://openreview.net/references/pdf?id="
FORUM_URL_PREFIX = "https://openreview.net/forum?id="

INVITATIONS = {
    f"iclr_{year}": f"ICLR.cc/{year}/Conference/-/Blind_Submission"
    for year in range(2018, 2025)
}

def is_review(note, conference):
    if conference == scc_lib.Conference.iclr_2023:
        return "Official_Review" in note.invitation
    elif conference == scc_lib.Conference.iclr_2022:
        return 'main_review' in note.content
    elif conference == scc_lib.Conference.iclr_2024:
        assert False
    else:
        return 'review' in note.content

# == Other helpers ===========================================================

Review = collections.namedtuple("Review",
                                "review_id sentences rating reviewer tcdate")


class ForumStatus(object):
    COMPLETE = "complete"
    NO_REVIEWS = "no_reviews"
    NO_PDF = "no_pdf"
    NO_REVISION = "no_revision"

def first_not_none(l):
    for x in l:
        if x is not None:
            return x
    assert False

# ============================================================================


def get_binary(note):
    try:  # try to get the PDF for this paper revision
        pdf_binary = GUEST_CLIENT.get_pdf(note.id, is_reference=True)
        pdf_status = PDFStatus.AVAILABLE
    except openreview.OpenReviewException as e:
        pdf_status = PDF_ERROR_STATUS_LOOKUP[e.args[0]["name"]]
        pdf_binary = None
    return pdf_status, pdf_binary


def write_pdfs(forum_dir, initial_binary, final_binary):
    for binary, version in [(initial_binary, scc_lib.INITIAL),
                            (final_binary, scc_lib.FINAL)]:
        assert binary is not None
        with open(f'{forum_dir}/{version}.pdf', "wb") as f:
            f.write(binary)


def get_last_valid_reference(references):
    for r in reversed(references):
        status, binary = get_binary(r)
        if status == PDFStatus.AVAILABLE:
            return (r, binary)
    return None, None


def get_review_sentences_and_rating(note, conference):
    """Get raw review text. Review text field differs between years.
    """
    if conference == scc_lib.Conference.iclr_2023:
        review_text = "\n".join(
            [note.content[key]
                for key in [
                    "strengths_and_weaknesses"
                    # TODO: find the other fields
                ]]
        rating = note.content['recommendation']
    elif conference == scc_lib.Conference.iclr_2022:
        review_text = note.content['main_review']
        rating = note.content['recommendation']
    elif conference == scc_lib.Conference.iclr_2024:
        assert False
    else:
        review_text = note.content['review']
        rating = note.content['rating']

    return [
        sent.text
        for sent in scc_lib.SENTENCIZE_PIPELINE(review_text).sentences
    ], rating


def write_metadata(forum_dir, forum, conference, initial_id, final_id,
                   decision, review_notes):
    reviews = []
    for review_note in review_notes:
        review_sentences, rating = get_review_sentences_and_rating(review_note,
        conference)
        reviews.append(
            Review(review_note.id, review_sentences, rating,
                   export_signature(review_note),
                   review_note.tcdate)._asdict())
    with open(f'{forum_dir}/metadata.json', 'w') as f:
        f.write(
            json.dumps(
                {
                    'identifier': forum.id,
                    'reviews': reviews,
                    'decision': decision,
                    'conference': conference,
                    'urls': {
                        'forum': f'{FORUM_URL_PREFIX}{forum.id}',
                        'initial': f'{PDF_URL_PREFIX}{initial_id}',
                        'final': f'{PDF_URL_PREFIX}{final_id}',
                    }
                },
                indent=2))


def process_forum(forum, conference, output_dir):

    # === Get all notes, reviews, decisions, etc ==============================

    forum_notes = GUEST_CLIENT.get_all_notes(forum=forum.id)

    # Retrieve all reviews from the forum
    review_notes = [
        note for note in forum_notes if is_review(note, conference)
        ]
        # The conditions that make a note a review differ from year to year.
        
    # Retrieve decision
    decisions = first_not_none([
        note.content.get('decision', None)
        for note in forum_notes
    ])

    # e.g. If the paper was withdrawn
    if not review_notes:
        return ForumStatus.NO_REVIEWS, decision

    # === Get `initial' and `final' pdfs ======================================

    # Retrieve all revisions of the manuscript in order of submission
    references = sorted(GUEST_CLIENT.get_all_references(referent=forum.id,
                                                        original=True),
                        key=lambda x: x.tcdate)

    # Valid references are those associated with a valid PDF.

    # --- final submission ----------------------------------------------------
    # The latest valid revision

    # The 'final' version is the latest valid version
    final_reference, final_binary = get_last_valid_reference(references)

    # --- initial submission --------------------------------------------------
    # The latest valid pre-review revision

    # Creation time of first review:
    # Changes made before this time cannot have been influenced by reviewers.
    first_review_time = min(rev.tcdate for rev in review_notes)

    references_before_review = [
        r for r in references if r.tcdate <= first_review_time
    ]
    # The initial revision is the latest valid revision of the list above
    initial_reference, initial_binary = get_last_valid_reference(
        references_before_review)

    # === Finalize ============================================================

    # Proceed only for forums with valid and distinct initial and final
    # versions
    if final_reference is not None and initial_reference is not None:
        if not final_reference.id == initial_reference.id:

            # Create subdirectory
            forum_dir = f'{output_dir}/{forum.id}'
            os.makedirs(forum_dir, exist_ok=True)

            # Write pdfs and metadata
            write_pdfs(forum_dir, initial_binary, final_binary)
            write_metadata(forum_dir, forum, conference, initial_reference.id,
                           final_reference.id, decision, review_notes)

            return ForumStatus.COMPLETE, decision
        else:
            # Manuscript was not revised after the first review
            return ForumStatus.NO_REVISION, decision
    else:
        # No versions associated with valid PDFs were found
        return ForumStatus.NO_PDF, decision


def main():

    args = parser.parse_args()

    # A directory will be made for each paper submission under the output directory.
    os.makedirs(args.output_dir, exist_ok=True)

    statuses = []
    
    # Gets top level notes for each `forum' (each paper submission is assigned
    # a forum)
    forum_notes = GUEST_CLIENT.get_all_notes(
        invitation=INVITATIONS[args.conference])

    # Hack for --debug    
    success_count = 0

    for forum in tqdm.tqdm(forum_notes):
        # Process a forum. As a side effect, write pdfs to directory.
        status, decision = process_forum(forum, args.conference,
                                          args.output_dir)
        statuses.append((forum.id, status, decision))
    
        # === --debug stuff ===
        if status == ForumStatus.COMPLETE:
            success_count += 1
        if args.debug and success_count == 10 or len(statuses) > 100:
            break
        # === end --debug stuff ===


    # Write all statuses to file.
    # TODO: determine if useful to do while processing rather than at the end.
    with open(f'{args.status_file_prefix}{args.conference}.tsv', 'w') as f:
        f.write('#Conference\tForum\tStatus\tDecision\n')
        for forum, status, decision in statuses:
            f.write(f'{args.conference}\t{forum}\t{status}\t{decision}\n')


if __name__ == "__main__":
    main()
