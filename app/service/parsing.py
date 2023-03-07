import os
import re
import docx2txt
import pandas as pd
from tempfile import NamedTemporaryFile

from app.logger import log
from app.utils import get_csv_dataset, to_csv_on_s3, create_s3fs
from app.config import settings
from app import model as m


TAGS = [("<q[0-9]*>", "</q[0-9]*>"), ("<a[0-9]*>", "</a[0-9]*>")]
COLUMNS = ["question", "answer", "file_info_id"]


def parse_text(file_info_id: int, text: str) -> pd.DataFrame:
    dict_with_res = dict()

    for open_tag, close_tag in TAGS:
        search_str = f"(?:{open_tag}.*?{close_tag})"
        q_and_a = re.finditer(search_str, text, flags=re.DOTALL)

        for val in q_and_a:
            value = val.group()
            tag_name = re.match(f"<({open_tag[1]}[0-9]*)>", value).group(1)
            str_from_value = re.match(
                f"{open_tag}(.*){close_tag}", value, flags=re.DOTALL
            ).group(1)

            if tag_name.startswith("q"):
                dict_with_res[tag_name] = (str_from_value, None, file_info_id)
            elif tag_name.startswith("a"):
                try:
                    suitable_question = f"q{tag_name[1:]}"
                    dict_with_res[suitable_question] = (
                        dict_with_res[suitable_question][0],
                        str_from_value,
                        dict_with_res[suitable_question][2],
                    )
                except Exception as err:
                    log(log.ERROR, "The error occured: [%s]", err)

    results_df = pd.DataFrame(data=dict_with_res.values(), columns=COLUMNS)
    return results_df


def parse_document(file_data: m.UploadedFile):
    """
    This function retrieve unprocessed document from S3 bucket, parse it and
    append new information to dataset.csv of company

    Args:
        file_data (m.UploadedFile): data about the file from db
    """

    # Create S3FileSystem connection
    s3_fs = create_s3fs()
    s3_path = os.path.join(settings.S3_BUCKET_NAME, file_data.s3_relative_path)

    with s3_fs.open(s3_path, mode="rb") as document:
        doc = docx2txt.process(document)

    s3_fs.rm(s3_path)

    df = get_csv_dataset(s3_fs, file_data.company_id, COLUMNS)

    results_df = parse_text(file_data.id, doc)

    new_df = pd.concat([df, results_df])

    to_csv_on_s3(s3_fs, new_df, file_data.company_id)

    log(log.INFO, "Parsing succeed for [%s]", file_data.filename)


# To test different parsing algorithms
def parse_local_document():
    """Just a function for local testing of documents parsing"""
    filename = "app/uploaded_docs/Expression of Interest Form - Tier 3 Weight Management Service.docx"
    doc = docx2txt.process(filename)

    df = pd.DataFrame(columns=COLUMNS)

    results_df = parse_text(doc)

    new_df = pd.concat([df, results_df])

    new_df.to_csv(
        "/home/danil/simple2b/bidhive/bidhive-ml-api/app/uploaded_docs/dataset.csv"
    )

    log(log.INFO, "Parsing succeed")
