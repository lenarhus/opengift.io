__author__ = 'Gvammer'
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils import simplejson
from django.template import Library
register = Library()


@register.filter(name='json')
def json(object):
    return simplejson.dumps(object)

@register.filter(name='jsonify')
def jsonify(object):
    if isinstance(object, QuerySet):
        return serialize('json', object)
    return simplejson.dumps(object)
