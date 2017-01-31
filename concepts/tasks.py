from __future__ import absolute_import

import requests

from concepts.authorities import resolve, search



def resolve_concept(sender, instance):
    try:
        resolve(sender, instance)
    except requests.exceptions.ConnectionError:
        pass


def search_concept(query, pos='noun'):
    try:
        search(query, pos)
    except requests.exceptions.ConnectionError:
        pass
