from sklearn.feature_extraction.text import CountVectorizer
from pymystem3 import Mystem


simple_tokenizer = CountVectorizer(lowercase=False, token_pattern='\w+').build_analyzer()
mystem = Mystem()

stop_pos_tags = [
    'ADVPRO',
    'APRO',
    'CONJ',
    'INTJ',
    'PART',
    'PR',
    'SPRO',
    'V',
    'ADV'
]


def tokenize(text):
    return (' '.join(simple_tokenizer(text)))


def lemmatize(text):
    return ''.join(mystem.lemmatize(tokenize(text))).strip()


def nominalize(text):
    an = mystem.analyze(text)
    filtered_tokens = []
    for ta in an:
        if 'analysis' in ta:
            if not ta['analysis']:
                filtered_tokens.append(ta['text'])
                continue
            pos_tag = ta['analysis'][0]['gr'].split(',', 1)[0].split('=', 1)[0]
            if pos_tag not in stop_pos_tags:
                filtered_tokens.append(ta['text'])
    return ' '.join(filtered_tokens)
