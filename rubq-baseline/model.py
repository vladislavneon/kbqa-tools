from time import sleep
import requests
from entity_recognition import EntityRecognizer
from entity_linking import EntityLinker
from property_extraction import PropertyExtractor
from query_generation import QueryGenerator


class RuBQBaseline:
    def __init__(self, syntactic_parser, es_instance, index_name='wikidata_entities', sparql_executor=None):
        self.entity_recognizer = EntityRecognizer(syntactic_parser)
        self.entity_linker = EntityLinker(es_instance, index_name)
        self.property_exctractor = PropertyExtractor()
        self.query_generator = QueryGenerator()
        self._execute_query = sparql_executor if sparql_executor else KBQAModel.execute_query

    @staticmethod
    def execute_query(query):
        sleep(0.75)
        response = requests.get('https://query.wikidata.org/sparql', params={'format': 'json', 'query': query})
        to_sleep = 3
        while response.status_code == 429:
            sleep(to_sleep)
            to_sleep += 2
            response = requests.get('https://query.wikidata.org/sparql', params={'format': 'json', 'query': query})
            print('slept')
        answers = response.json()['results']['bindings']
        res = [ans['answer'] for ans in answers]
        return res

    def answer(self, question):
        entities_spans = self.entity_recognizer.find_entities_spans(question)
        candidate_entities = self.entity_linker.get_candidate_entities(entities_spans)
        candidate_properties = self.property_exctractor.extract_properties(question)
        queries = self.query_generator.generate_queries(candidate_entities, candidate_properties)
        for query in queries:
            response = self._execute_query(query)
            if response:
                return response
        return []
