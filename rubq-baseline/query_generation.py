from operator import itemgetter


class QueryGenerator:
    def _order_entities(self, linking):
        merged_linking = {
            'full': [],
            'ngram': [],
            'cap': [],
            'ft': []
        }
        for item in linking:
            merged_linking['full'].extend(item['full'])
            merged_linking['ngram'].extend(item['ngram'])
            merged_linking['cap'].extend(item['cap'])
            if 'ft' in item:
                merged_linking['ft'].extend(item['ft'])
        for t, ents in merged_linking.items():
            merged_linking[t] = sorted(ents, key=itemgetter(2), reverse=True)
        all_entities = merged_linking['full'] + \
                       merged_linking['ngram'] + \
                       merged_linking['cap'] + \
                       merged_linking['ft']
        res = []
        qids = set()
        for ent in all_entities:
            if ent[0] not in qids:
                qids.add(ent[0])
                res.append(ent)
        return res

    def _build_query(self, qid, pid):
        return f'''
    SELECT ?answer 
    WHERE {{
      wd:{qid} wdt:{pid} ?answer
    }}
    '''

    def generate_queries(self, candidate_entities, candidate_properties):
        queries = []
        candidate_entities = self._order_entities(candidate_entities)
        for entity in candidate_entities:
            for property in candidate_properties:
                qid = entity[0]
                query = self._build_query(qid, property)
                queries.append(query)
        return queries
