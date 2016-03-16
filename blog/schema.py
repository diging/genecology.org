import rdflib
from rdflib.term import URIRef
from models import RDFSchema, RDFProperty, RDFClass
from itertools import chain

TITLE = URIRef('http://purl.org/dc/terms/title')
PROPERTY = URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#Property')
TYPE = URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
CLASS = URIRef('http://www.w3.org/2000/01/rdf-schema#Class')
OWL_CLASS = URIRef('http://www.w3.org/2002/07/owl#Class')
DESCRIPTION = URIRef('http://purl.org/dc/terms/description')
COMMENT = URIRef('http://www.w3.org/2000/01/rdf-schema#comment')

LABEL = URIRef('http://www.w3.org/2000/01/rdf-schema#label')
RANGE = URIRef('http://www.w3.org/2000/01/rdf-schema#range')
DOMAIN = URIRef('http://www.w3.org/2000/01/rdf-schema#domain')
SUBPROPERTYOF = URIRef('http://www.w3.org/2000/01/rdf-schema#subPropertyOf')
SUBCLASSOF = URIRef('http://www.w3.org/2000/01/rdf-schema#subClassOf')


def _get_object(g, s, p):
    """
    Retrieve the (first) object of a relation. This is mainly to be used where
    we expect only one relation of the specified type.

    Parameters
    ----------
    g : rdflib.Graph
    s : rdflib.term.URIRef
        The subject of the relation.
    p : rdflib.term.URIRef
        The predicate of the relation.

    Returns
    -------
    rdflib.term.URIRef
    """

    # objects() will return an empty iterator if the predicate is not found.
    try:
        return list(g.objects(s, p))[0]
    except IndexError:
        return None


def _get_label(g, s):
    """
    Try to find the English label. Short of that, choose the first label.
    """
    try:
        for label in g.objects(s, LABEL):
            if label.language == 'en':
                return label
        return list(g.objects(s, LABEL))[0]
    except IndexError:
        return _identifier(s)


def _identifier(uri_ref):
    """
    Grab the identifier from a URIRef.

    Parameters
    ----------
    uri_ref : rdflib.term.URIRef

    Returns
    -------
    unicode
    """
    if '#' in uri_ref:
        delim = '#'
    else:
        delim = '/'
    return unicode(uri_ref).split(delim)[-1]


def import_schema(schema_url, schema_name):
    g = rdflib.Graph()
    # Load RDF from remote location.
    g = rdflib.Graph()
    try:
        g.parse(schema_url)
    except:
        g.parse(schema_url, format='xml')

    schema = RDFSchema(name=schema_name, uri=schema_url)
    schema.save()

    # Literal is an RDFClass, too! At least it's easier, that way.
    defaults = {'label': u'Literal', 'partOf': schema}
    literal_instance = RDFClass.objects.get_or_create(identifier=u'Literal',
                                                      defaults=defaults)[0]

    # Some schemas use the OWL Class type.
    classes = chain(g.subjects(TYPE, CLASS), g.subjects(TYPE, OWL_CLASS))
    properties = g.subjects(TYPE, PROPERTY)

    subClass_relations, subProperty_relations = [], []
    classesHash, propertiesHash = {}, {}

    # We index the Literal RDFClass so that we can retrieve it when populating
    #  domain and range fields on RDFProperty instances.
    classesHash[u'Literal'] = literal_instance

    # Build RDFClasses first, so that we can use them in the domain and range
    #  of RDFProperty instances.
    for class_ref in classes:
        identifier = _identifier(class_ref)

        # We prefer to use the description, but comment is fine, too.
        comment = _get_object(g, class_ref, DESCRIPTION)
        if not comment:
            comment = _get_object(g, class_ref, COMMENT)

        kwargs = {
            'identifier': identifier,
            'defaults': {
                'comment': comment,
                'label': _get_label(g, class_ref),
                'partOf': schema,
            }
        }
        instance, created = RDFClass.objects.get_or_create(**kwargs)
        classesHash[identifier] = instance

        # We defer filling subClassOf on the model instances until after we have
        #  created all of the instances.
        subClassOf = _get_object(g, class_ref, SUBCLASSOF)
        if subClassOf:
            subClass_relations.append((identifier, _identifier(subClassOf)))

    # Fill in subClass relations on the model instances.
    for source, target in subClass_relations:
        classesHash[source].subClassOf = classesHash[target]
        classesHash[source].save()

    # Now generate RDFProperty instances.
    for property_ref in properties:
        identifier = _identifier(property_ref)

        # We prefer to use the description, but comment is fine, too.
        comment = _get_object(g, property_ref, DESCRIPTION)
        if not comment:
            comment = _get_object(g, property_ref, COMMENT)

        kwargs = {
            'identifier': identifier,
            'defaults': {
                'comment': comment,
                'label': _get_label(g, property_ref),
                'partOf': schema,

            }
        }
        instance, created = RDFProperty.objects.get_or_create(**kwargs)


        instance.domain = classesHash[_identifier(_get_object(g, property_ref, DOMAIN))]

        try:
            range_ref = _get_object(g, property_ref, RANGE)
            rclass = classesHash[_identifier(range_ref)]
        except KeyError:
            rclass = RDFClass.objects.get_or_create(
                        identifier=_identifier(range_ref),
                        defaults={'partOf': schema})[0]
        instance.range = rclass
        instance.save()
        propertiesHash[identifier] = instance

        # We defer filling subPropertyOf on the model instances until after we
        #  have created all of the instances.
        subPropertyOf = _get_object(g, class_ref, SUBPROPERTYOF)
        if subPropertyOf:
            subProperty_relations.append((identifier, _identifier(subPropertyOf)))

    # Fill in the subPropertyOf field on RDFProperty instances.
    for source, target in subProperty_relations:
        propertiesHash[source].subPropertyOf = propertiesHash[target]
        propertiesHash[source].save()
