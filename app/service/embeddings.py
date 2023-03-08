import pandas as pd

# import tiktoken
import openai
from openai.embeddings_utils import get_embedding

from app.config import settings


openai.api_key = settings.OPENAI_API_KEY

# embedding model parameters
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_ENCODING = "cl100k_base"  # this the encoding for text-embedding-ada-002
MAX_TOKENS = 8000  # the maximum for text-embedding-ada-002 is 8191


def get_embeddings_for_df(df: pd.DataFrame):
    """
    Function for creating embeddings on the base of dataframe columns

    Args:
        df (pd.DataFrame): dataframe with parsed data

    Returns:
        df (pd.DataFrame): modified dataframe with embeddings
    """

    # TODO: use this to check amount of tokens in text
    # encoding = tiktoken.get_encoding(EMBEDDING_ENCODING)

    df["question_embedding"] = df.question.apply(
        lambda x: get_embedding(x, engine=EMBEDDING_MODEL)
    )
    # df["answer_embedding"] = df.answer.apply(lambda x: get_embedding(x, engine=EMBEDDING_MODEL))

    return df
