from textblob import TextBlob


def remove_quoted_text(s):
    state = 0  # 0: not in quotes, 1: in single quotes, 2: in double quotes
    result = []
    for char in s:
        if state == 0:
            if char == '"':
                state = 1
            else:
                result.append(char)
        elif state == 1:
            if char == '"':
                state = 0
    return ''.join(result)


def preprocess_text (text):
    text = remove_quoted_text (text)
    sentences = [sent for sent in text.split('.')
                 if TextBlob(sent).sentiment.subjectivity < 0.9]
    fact_text = '.'.join(sentences)
    return fact_text

