from operator import itemgetter
from helpers import json_read
from text_processing import tokenize, lemmatize, nominalize


class EntityLinker:
    def __init__(self, es_instance, index_name):
        self.es = es_instance
        self.index_name = index_name
        self.pageviews = json_read('pageviews_by_entity.json')

    def _get_query_results(self, query):
        res = self.es.search(index='all_entities', body=query, size=40)['hits']
        max_score = res['max_score']
        hits = res['hits']
        cands = []
        for hit in hits:
            if hit['_score'] < max_score:
                break
            qid = hit['_source']['qid']
            label = hit['_source']['label']
            views = self.pageviews[qid]
            cands.append((qid, label, views))
        return list(set(cands))

    def _reduce_cands(self, candidates):
        cand_qids = set()
        reduced_cands = []
        for cand in candidates:
            if cand[0] not in cand_qids:
                cand_qids.add(cand[0])
                reduced_cands.append(cand)
        return sorted(reduced_cands, key=itemgetter(2), reverse=True)

    def _get_span_candidates(self, span):
        candidates = {}

        full_candidates = []
        query = build_strict_query([span])
        full_candidates.extend(self._get_query_results(query))
        candidates['full'] = self._reduce_cands(full_candidates)

        ngram_candidates = []
        for n in range(5, 2, -1):
            ngrams = get_ngrams(span, n)
            for ngram in ngrams:
                query = build_strict_query([ngram])
                ngram_candidates.extend(self._get_query_results(query))
            if ngram_candidates:
                break
        candidates['ngram'] = self._reduce_cands(ngram_candidates)

        cap_candidates = []
        for cap_seq in get_capital_seqs(span):
            query = build_strict_query([cap_seq])
            cap_candidates.extend(self._get_query_results(query))
        if not cap_candidates:
            for cap in get_capital_words(span):
                query = build_strict_query([cap])
                cap_candidates.extend(self._get_query_results(query))
        candidates['cap'] = self._reduce_cands(cap_candidates)

        span = nominalize(span)
        query = build_disj_query([span])
        ft_candidates = self._get_query_results(query)
        candidates['ft'] = self._reduce_cands(ft_candidates)

        return candidates

    def get_candidate_entities(self, spans):
        cands = []
        for span in spans:
            cands.append(self._get_span_candidates(span))
        return cands


def get_ngrams(text, n=3):
    tokens = tokenize(text).split()
    res = []
    for i in range(len(tokens) - (n - 1)):
        res.append(' '.join(tokens[i:(i + n)]))
    return res


def is_capital_token(token):
    if token.isupper() and len(token) > 1:
        return False
    return token[0].isupper()


def is_abbr_token(token):
    return token.isupper() and len(token) > 1


def get_capital_seqs(text):
    tokens = tokenize(text).split()
    seqs = []
    pos = 0
    while pos < len(tokens):
        if is_abbr_token(tokens[pos]):
            seqs.append(tokens[pos])
            pos += 1
        elif is_capital_token(tokens[pos]):
            end = pos + 1
            while end < len(tokens):
                if not is_capital_token(tokens[end]):
                    break
                end += 1
            seqs.append(' '.join(tokens[pos:end]))
            pos = end + 1
        else:
            pos += 1
    return seqs


def get_capital_words(text):
    tokens = tokenize(text).split()
    words = []
    for token in tokens:
        if is_capital_token(token):
            words.append(token)
    return words


def build_strict_query(spans):
    queries = []
    for span in spans:
        queries.append({
            'match': {
                'label': {
                    'query': lemmatize(span),
                    'operator': 'AND',
                    "fuzziness": 'AUTO:5,15',
                    "prefix_length": 2,
                    'fuzzy_transpositions': False
                }
            }
        })
    return {
        'query': {
            'bool': {
                'should': queries
            }
        }
    }


def build_disj_query(spans):
    queries = []
    for span in spans:
        queries.append({
            'match': {
                'label': {
                    'query': lemmatize(span),
                    'operator': 'OR'
                }
            }
        })
    return {
        'query': {
            'bool': {
                'should': queries
            }
        }
    }
