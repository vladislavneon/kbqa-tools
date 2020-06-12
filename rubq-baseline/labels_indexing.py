from elasticsearch.helpers import parallel_bulk
from helpers import json_read


settings = {
    'mappings': {
        'properties': {
            'qid': {
                'type': 'keyword'
            },
            'label': {
                'type': 'text',
                'analyzer': 'white_lower'
            }
        }
    },
    'settings': {
        'analysis' : {
            'analyzer' : {
                'white_lower' : {
                    'tokenizer' : 'whitespace',
                    'filter' : ['lowercase']
                }
            }
        }
    }
}

def create_es_action(key, doc, index_name):
    es_action = {
        '_id': key,
        '_index': index_name,
        '_source': doc
    }
    return es_action


def action_generator(all_labels, index_name):
    for qid, lbls in all_labels.items():
        for i, lbl in enumerate(lbls):
            doc = {
                'qid': qid,
                'label': lbl
            }
            key = '.'.join([qid, str(i)])
            yield create_es_action(key, doc, index_name)


def index_labels(es_instance, labels_path='all_labels_lemmatized.json', index_name='wikidata_entities'):
    wikidata_labels = json_read(labels_path)
    es_instance.indices.create(index=index_name, body=settings)
    for ok, result in parallel_bulk(
            es_instance,
            action_generator(wikidata_labels, 'all_entities'),
            queue_size=8,
            thread_count=8,
            chunk_size=1000):
        if not ok:
            print(result)
