from sentence_transformers import SentenceTransformer


def check_contradiction ( text1 , text2 ):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    nli = pipeline('text-classification', model='roberta-large-mnli')
    nli_result = nli(text1, text_pair=text2)
    print (nli_result[0]['label'])

    return nli_result[0]['label']=='CONTRADICTION'

