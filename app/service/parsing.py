import os
import re
import docx2txt
import pandas as pd
import numpy as np
from s3fs import S3FileSystem

from app.logger import log
from app.utils import get_csv_dataset, to_csv_on_s3
from app.config import settings, COLUMNS
from app import model as m
from app.service.embeddings import get_embeddings_for_df


TAGS = [("<q[0-9]*>", "</q[0-9]*>"), ("<a[0-9]*>", "</a[0-9]*>")]


# TODO: The parsing logic would not work correctly if answer would be appear in text earlier than question
# TODO: how to deal with tables inside the questions or answers
# TODO: how to deal with lists and \n symbols in text
def parse_text(file_info_id: int, text: str) -> pd.DataFrame:
    """
    Function for parsing text data on the base of annotation tags

    Args:
        file_info_id (int): id of file data record in db (model UpladedFile)
        text (str): extracted text of word file (with docx2txt)

    Returns:
        pd.DataFrame: datagrame with parsed data
    """

    # Create for parsing results
    dict_with_res = dict()

    # Iterate on the list of TAGS
    for open_tag, close_tag in TAGS:
        search_str = f"(?:{open_tag}.*?{close_tag})"
        # Find all annotated information in recieved text
        q_and_a = re.finditer(search_str, text, flags=re.DOTALL)

        # Iterate on the list of searching results
        for val in q_and_a:
            value = val.group()
            # Extract key of tag to match questions and answers with each other: q1 -> a1
            tag_name = re.match(f"<({open_tag[1]}[0-9]*)>", value).group(1)
            # Extract just text without tags
            str_from_value = re.match(
                f"{open_tag}(.*){close_tag}", value, flags=re.DOTALL
            ).group(1)

            # Logic for questions
            if tag_name.startswith("q"):
                dict_with_res[tag_name] = (str_from_value, np.nan, file_info_id)
            # Logic for answers
            elif tag_name.startswith("a"):
                try:
                    suitable_question = f"q{tag_name[1:]}"
                    dict_with_res[suitable_question] = (
                        dict_with_res[suitable_question][0],
                        str_from_value,
                        dict_with_res[suitable_question][2],
                    )
                # Just log and pass if there is some answer that doesn't match any question
                except KeyError:
                    log(
                        log.INFO,
                        "There is no suitable question for these answer: [%s]",
                        tag_name,
                    )

    # Create dataframe with results and drop all rows where answer is abcent
    results_df = pd.DataFrame(data=dict_with_res.values(), columns=COLUMNS[:3])
    results_df.dropna(subset=["answer"], inplace=True)
    return results_df


def parse_document(file_data: m.UploadedFile, s3_fs: S3FileSystem):
    """
    This function retrieve unprocessed document from S3 bucket, parse it and
    append new information to dataset.csv of company

    Args:
        file_data (m.UploadedFile): data about the file from db
    """

    # Create S3FileSystem connection, retrieve info from file and then delete it
    s3_path = os.path.join(settings.S3_BUCKET_NAME, file_data.s3_relative_path)
    with s3_fs.open(s3_path, mode="rb") as document:
        doc = docx2txt.process(document)
    s3_fs.rm(s3_path)

    df = get_csv_dataset(s3_fs, file_data.company_id, COLUMNS)
    results_df = parse_text(file_data.id, doc)

    # Create embeddings for questions and answers
    results_df = get_embeddings_for_df(results_df)

    # Append dataset with new information to existing company dataset
    new_df = pd.concat([df, results_df])
    new_df.reset_index(drop=True, inplace=True)

    # Upload extended dataframe on S3 bucket
    to_csv_on_s3(s3_fs, new_df, file_data.company_id)

    log(log.INFO, "Parsing succeed for [%s]", file_data.filename)


# NOTE: To test different parsing algorithms
def parse_local_document():
    """Just a function for local testing of documents parsing"""
    filename = "tests/test_files/Expression of Interest Form - Tier 3 Weight Management Service.docx"
    doc = docx2txt.process(filename)

    if os.path.exists(
        "/home/danil/simple2b/bidhive/bidhive-ml-api/app/uploaded_docs/dataset.csv"
    ):
        df = pd.read_csv(
            "/home/danil/simple2b/bidhive/bidhive-ml-api/app/uploaded_docs/dataset.csv",
            index_col=0,
        )
    else:
        df = pd.DataFrame(columns=COLUMNS)

    results_df = parse_text(0, doc)

    new_df = pd.concat([df, results_df])
    new_df.reset_index(drop=True, inplace=True)

    # new_df.to_csv(
    #     "/home/danil/simple2b/bidhive/bidhive-ml-api/app/uploaded_docs/dataset.csv"
    # )

    log(log.INFO, "Parsing succeed")
