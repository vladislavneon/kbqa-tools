import re
from functools import reduce
from operator import concat, itemgetter
from conllu import parse_tree
from helpers import json_read
from text_processing import tokenize


class SynTree:
    ignored_deprels = ['punct', 'cop']

    def __init__(self, token_tree):
        self.tree = token_tree

    def __getattr__(self, attr):
        return getattr(self.tree, attr)

    def _walk(self, m, f, e0):
        def _dfs(v):
            return f(m(v), reduce(f, map(_dfs, v.children), e0))

        return _dfs(self.tree)

    def has_nth_token(self, n):
        return self._walk(lambda t: t.token['id'] == n, lambda x, y: x or y, False)

    def has_token(self, token):
        return self._walk(lambda t: t.token['form'] == token, lambda x, y: x or y, False)

    def ignored(self):
        return self.tree.token['deprel'] in type(self).ignored_deprels

    def get_ordered_tokens(self):
        return self._walk(lambda t: [(t.token['id'], t.token['form'])], concat, [])


class EntityRecognizer:
    def __init__(self, syntactic_parser):
        self.question_words = json_read('question_words.json')
        self.syntactic_parser = syntactic_parser

    def _extract_question_word(self, text):
        text = tokenize(text)
        for qw in self.question_words:
            q_phrase = re.match(qw['re'], text, re.IGNORECASE)
            if q_phrase:
                q_word = qw['word']
                break
        q_phrase = q_phrase.group(0)
        return re.search(q_word, q_phrase, re.IGNORECASE).group(0)

    def _get_synt_parse(self, text):
        return self.syntactic_parser(text)

    def find_entities_spans(self, question):
        q_word = self._extract_question_word(question)
        syntax_parse = self._get_synt_parse(question)
        root = parse_tree(syntax_parse)[0]
        if root.token['form'] == q_word:
            for t in root.children:
                if t.token['deprel'] == 'nsubj':
                    root = t
                    break

        entity_tokens = []
        for t in root.children:
            syntree = SynTree(t)
            if not syntree.has_token(q_word) and not syntree.ignored():
                entity_tokens.append(syntree.get_ordered_tokens())

        if not entity_tokens:
            spans = []
        else:
            spans = [' '.join(list(zip(*sorted(et, key=itemgetter(0))))[1]) for et in entity_tokens]

        return spans

