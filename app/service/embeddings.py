import pandas as pd
import numpy as np

# import tiktoken
import openai
from openai.embeddings_utils import get_embedding, cosine_similarity, aget_embedding

from app.config import settings
from app.logger import log


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
    # TODO: deal with really long texts that longer than 8192 tokens
    # encoding = tiktoken.get_encoding(EMBEDDING_ENCODING)

    df["question_embedding"] = df.question.apply(
        lambda x: get_embedding(x, engine=EMBEDDING_MODEL)
    )

    # NOTE: Not sure that we need to create embeddings on the base of answers
    # df["answer_embedding"] = df.answer.apply(
    #     lambda x: get_embedding(x, engine=EMBEDDING_MODEL)
    # ).apply(np.array)

    log(log.DEBUG, "Question embaddings created")
    return df


def search_answers(df: pd.DataFrame, search_prompt: str, n: int = 1):
    """
    Searching over the dataframe with embeddings

    Args:
        df (pd.DataFrame): dataframe with question embeddings
        search_prompt (str): user's search prompt
        n (int, optional): amount of closest matches to return

    Returns:
        df (pd.Dataframe): dataframe with closest matches
    """
    log(log.DEBUG, "Answer searching start for prompt [%s]", search_prompt)
    # Create embedding for search prompt
    prompt_embedding = get_embedding(search_prompt, engine=EMBEDDING_MODEL)
    df["question_embedding"] = df.question_embedding.apply(eval).apply(np.array)
    df["similarity"] = df.question_embedding.apply(
        lambda x: cosine_similarity(x, prompt_embedding)
    )

    results = df.sort_values("similarity", ascending=False).head(n)

    log(log.INFO, "Answer searching secceed for prompt [%s]", search_prompt)
    return results
