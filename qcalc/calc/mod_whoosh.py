# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from whoosh.fields import Schema, TEXT, ID, KEYWORD, STORED
from whoosh.index import create_in, open_dir
from whoosh.filedb.filestore import RamStorage
from whoosh.analysis import StemmingAnalyzer
import os
import re
from django.conf import settings
from .mod_qcals import QCals
from whoosh.qparser import QueryParser, FuzzyTermPlugin, DisMaxParser, QueryParserError
from qcore import QScreen
from whoosh import scoring


class QSearch:
    @classmethod
    def __init__(cls, mode='f', create=False):
        cls.mode = mode
        if mode == 'f' and not create:
            cls.ix = get_file_ix()

        if create:
            cls.ix = cls.create_search_index()

    @classmethod
    def create_search_index(cls):  # f=file, m=memory
        schema = Schema(
            id=ID(stored=True),
            name=TEXT(stored=True),
            title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            desc=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            tags=KEYWORD(stored=True, commas=True, lowercase=True, analyzer=StemmingAnalyzer()),
            node_type=STORED()
        )

        if cls.mode == 'f':
            ix = create_file_index(schema)
        else:
            ix = create_in_memory_index(schema)
        writer = ix.writer()

        # Add documents
        calc_nodes = QCals.calc_root.get_tree()
        pcalc_nodes = QCals.pcalc_root.get_tree()
        qty_nodes = QCals.qty_root.get_tree()

        for node in calc_nodes + pcalc_nodes + qty_nodes:
            writer.add_document(
                id=node.id,
                name=node.name,
                title=node.title,
                desc=node.desc,
                tags=node.tags,
                node_type=node.node_type
            )
        writer.commit()
        return ix

    @classmethod
    def perform_search(cls, query_string: str, idonly=False):
        query_string = (query_string or '').strip()
        if not query_string:
            return []

        # with cls.ix.searcher() as searcher:
        # with cls.ix.searcher(weighting=scoring.BM25F()) as searcher:
        # Use BM25F for relevance scoring, with field boosting
        fieldboosts = {
            "id": 3.0,
            "name": 2.5,
            "title": 2.0,
            "tags": 1.5,
            "desc": 1.1
        }
        _fields = fieldboosts.keys()
        with cls.ix.searcher(weighting=scoring.BM25F(field_B=fieldboosts)) as searcher:
            if idonly:
                parser = QueryParser("id", schema=cls.ix.schema)
                parsed_string = query_string
            else:
                parser = DisMaxParser(fieldboosts, schema=cls.ix.schema)  # MultifieldParser, fields, group=OrGroup
                parsed_string = query_string

            results_list, results = cls._run_query(searcher, parser, parsed_string)

            # | Free-text search terms may collide with Whoosh query syntax (quotes,
            # | colons, wildcards, unbalanced parens) - fall back to an escaped,
            # | plain-text query instead of letting a QueryParserError bubble up.
            if results is None:
                escaped = re.sub(r'[^\w\s]', ' ', query_string).strip()
                results_list, results = cls._run_query(searcher, parser, escaped, safe=True)

            # | Zero-hit exact search - retry once with fuzzy matching so minor
            # | typos still surface results.
            if not idonly and not results_list:
                fuzzy_parser = DisMaxParser(fieldboosts, schema=cls.ix.schema)
                fuzzy_parser.add_plugin(FuzzyTermPlugin())
                fuzzy_string = ' '.join([f'{word}~1/1' for word in query_string.split()])
                results_list, results = cls._run_query(searcher, fuzzy_parser, fuzzy_string, safe=True)

        return results_list

    @classmethod
    def _run_query(cls, searcher, parser, parsed_string, safe=False):
        # | Returns (results_list, results) - results is None only when the
        # | initial (non-safe) parse itself failed, signalling the caller to retry.
        try:
            query = parser.parse(parsed_string)
        except QueryParserError:
            if safe:
                return [], []
            return [], None
        results = searcher.search(query, limit=20)  # Limit results to top 20 for performance
        # | Convert results to a list of dictionaries (+ relevance score) to use outside searcher
        results_list = [{**dict(result), 'score': result.score} for result in results]
        return results_list, results


def search_result_nodes(results, scope='cx'):
    calc_nodes = []
    pcalc_nodes = []
    unit_nodes = []
    for result in results:
        id_ = result['id']
        node_type = result['node_type']
        if node_type == 'c' and 'c' in scope:
            node = QCals.calc_root.get_node_by_id(id_)
            if node:
                calc_nodes.append(node)
            else:
                node = QCals.pcalc_root.get_node_by_id(id_)
                if node: pcalc_nodes.append(node)
        elif 'x' in scope:  # 'u', 'q'
            node = QCals.qty_root.get_node_by_id(id_)
            unit_nodes.append(node)
    return calc_nodes, pcalc_nodes, unit_nodes


def print_search_result(results):
    out = QScreen()
    for result in results:
        out.write(f"Id: {result['id']}")
        out.write(f"Name: {result['name']}")
        out.write(f"Title: {result['title']}")
        out.write(f"Description: {result['desc']}")
        out.write(f"Tags: {result['tags']}")
        out.write()
    return out.flush()


# Create an in-memory index using RamStorage
def create_in_memory_index(schema):
    ram_storage = RamStorage()
    ix = ram_storage.create_index(schema)
    return ix


def get_file_ix():
    index_dir = settings.FILE_UPLOAD_TEMP_DIR + "search"
    ix = open_dir(index_dir)
    return ix


def create_file_index(schema):
    index_dir = settings.FILE_UPLOAD_TEMP_DIR + "search"
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    # Create the index
    ix = create_in(index_dir, schema)
    return ix


def _test():
    QSearch('m', True)
    results = QSearch.perform_search('earth mass')
    content = print_search_result(results)
    print(content)

    results = QSearch.perform_search('mass earth')
    content = print_search_result(results)
    print(content)

    results = QSearch.perform_search('body mass')
    content = print_search_result(results)
    print(content)


if __name__ == '__main__':
    _test()
