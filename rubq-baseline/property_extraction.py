import re
from helpers import json_read


class PropertyExtractor:
    def __init__(self):
        self.rules = json_read('properties_rules.json')

    def extract_properties(self, question):
        properties = []
        for reg in self.rules:
            if re.search(reg, question):
                properties.extend(self.rules[reg])
        return properties
