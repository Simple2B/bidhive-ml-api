import docx2txt
import pytest

from app.service import parse_text, get_embeddings_for_df


# NOTE: this test works with real OpenAI API, so use it just manualy
@pytest.mark.skip
def test_get_embeddings_for_df():
    filename = "tests/test_files/Expression of Interest Form - Tier 3 Weight Management Service.docx"
    doc = docx2txt.process(filename)

    results_df = parse_text(0, doc)
    df_with_emb = get_embeddings_for_df(results_df)
    print(df_with_emb)

    assert "question_embedding" in df_with_emb
