import re
import docx2txt
import pandas as pd
from tempfile import NamedTemporaryFile

from app.logger import log
from app.utils import create_or_retriev_csv, to_csv_on_s3, create_s3_resource
from app.config import settings


my_tags = [("<q[0-9]*>", "</q[0-9]*>"), ("<a[0-9]*>", "</a[0-9]*>")]


def parse_document(file_data):
    """
    This function retrieve unprocessed document from S3 bucket, parse it and
    append new information to dataset.csv of company

    Args:
        file_data (_type_): the instance from model UploadedFile
    """
    s3_resource = create_s3_resource()
    file = s3_resource.Object(
        bucket_name=f"{settings.S3_BUCKET_NAME}",
        key=f"{file_data.company_id}/{file_data.filename}",
    )

    with NamedTemporaryFile() as tmp:
        file.download_fileobj(tmp)
        doc = docx2txt.process(tmp.name)

    file.delete()

    df = create_or_retriev_csv(file_data.company_id)

    dict_with_res = dict()

    for open_tag, close_tag in my_tags:
        search_str = f"(?:{open_tag}.*?{close_tag})"
        q_and_a = re.finditer(search_str, doc, flags=re.DOTALL)

        for val in q_and_a:
            value = val.group()
            tag_name = re.match(f"<({open_tag[1]}[0-9]*)>", value).group(1)
            str_from_value = re.match(
                f"{open_tag}(.*){close_tag}", value, flags=re.DOTALL
            ).group(1)

            if tag_name.startswith("q"):
                dict_with_res[tag_name] = (str_from_value, None)
            elif tag_name.startswith("a"):
                try:
                    suitable_question = f"q{tag_name[1:]}"
                    dict_with_res[suitable_question] = (
                        dict_with_res[suitable_question][0],
                        str_from_value,
                    )
                except Exception as err:
                    log(log.ERROR, "The error occured: [%s]", err)

    results_series = pd.DataFrame(
        data=dict_with_res.values(), columns=["question", "answer"]
    )

    new_df = pd.concat([df, results_series])

    to_csv_on_s3(new_df, file_data.company_id)

    log(log.INFO, "Parsing succeed for [%s]", file_data.filename)
