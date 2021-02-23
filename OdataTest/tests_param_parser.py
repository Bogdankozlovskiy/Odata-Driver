from django.test import TestCase
from django.db import models
from django.db.models import functions
from urllib.parse import quote, parse_qs
from OdataTest.odata_param_parser import django_params


FILTER_TESTS = [
    (
        {"$filter": "foo eq '1'"},
        {"filter": models.Q(foo='1')}
    ),
    (
        {"$filter": "foo eq 1"},
        {"filter": models.Q(foo=1)}
    ),
    (
        {"$filter": "Address/City ne 'London'"},
        {"filter": ~models.Q(Address__City='London')}
    ),
    (
        {"$filter": "start_date gt '2017-03-01'"},
        {"filter": models.Q(start_date__gt='2017-03-01')}
    ),
    (
        {"$filter": "Price lt '20'"},
        {"filter": models.Q(Price__lt='20')}
    ),
    (
        {"$filter": "Price lt 20"},
        {"filter": models.Q(Price__lt=20)}
    ),
    (
        {"$filter": "Price le '100'"},
        {"filter": models.Q(Price__lte='100')}
    ),
    (
        {"$filter": "Price le 100"},
        {"filter": models.Q(Price__lte=100)}
    ),
    (
        {"$filter": "start_date ge '2017-03-01' and start_date lt '2017-03-02'"},
        {"filter": models.Q(start_date__gte='2017-03-01') & models.Q(start_date__lt='2017-03-02')}
    ),
    (
        {"$filter": "location/postal_code eq '22980'"},
        {"filter": models.Q(location__postal_code='22980')}
    ),
    (
        {"$filter": "location/postal_code eq 22980"},
        {"filter": models.Q(location__postal_code=22980)}
    ),
    (
        {"$filter": "contains(name, 'Sessions') or contains(name, 'DeVos')"},
        {"filter": models.Q(name__contains="Sessions") | models.Q(name__contains="DeVos")}
    ),
    (
        {"$filter": "location/postal_code eq '22980' and (contains(name, 'Session') or contains(name, 'DeVos'))"},
        {
            "filter": models.Q(location__postal_code='22980') & (
                    models.Q(name__contains="Session") | models.Q(name__contains="DeVos"))
        }
    ),
    (
        {"$filter": "location/postal_code eq 22980 and (contains(name, 'Session') or contains(name, 'DeVos'))"},
        {
            "filter": models.Q(location__postal_code=22980) & (
                    models.Q(name__contains="Session") | models.Q(name__contains="DeVos"))
        }
    ),
    (
        {"$filter": "(contains(name, 'Session') or contains(name, 'DeVos')) and location/postal_code eq '22980'"},
        {
            "filter": (models.Q(name__contains="Session") | models.Q(name__contains="DeVos")) & models.Q(
                location__postal_code="22980")
        }
    ),
    (
        {"$filter": "(contains(name, 'Sess') or contains(name, 'DeVos')) and location/postal_code eq 22980"},
        {
            "filter": (models.Q(name__contains="Sess") | models.Q(name__contains="DeVos")) & models.Q(
                location__postal_code=22980
            )
        }
    ),
    (
        {"$filter": "not contains(name, 'Sessions')"},
        {"filter": ~models.Q(name__contains="Sessions")}
    ),
    (
        {"$filter": "endswith(Description,'milk')"},
        {"filter": models.Q(Description__endswith="milk")}
    ),
    (
        {"$filter": "not endswith(Description,'milk')"},
        {"filter": ~models.Q(Description__endswith="milk")}
    ),
    (
        {"$filter": "substringof('Sessions', name) or substringof('DeVos', name)"},
        {"filter": models.Q(name__contains="Sessions") | models.Q(name__contains="DeVos")}
    ),
    (
        {"$filter": "startswith(Description,'milk')"},
        {"filter": models.Q(Description__startswith="milk")}
    ),
    (
        {"$filter": "length(Name) eq '5'"},
        {"filter": models.Q(Name__length='5')}
    ),
    (
        {"$filter": "year(DateOfBirth) eq '1990'"},
        {"filter": models.Q(DateOfBirth__year='1990')}
    ),
    (
        {"$filter": "month(DateOfBirth) eq '5'"},
        {"filter": models.Q(DateOfBirth__month='5')}
    ),
    (
        {"$filter": "day(DateOfBirth) eq '31'"},
        {"filter": models.Q(DateOfBirth__day='31')}
    ),
    (
        {"$filter": "hour(DateOfBirth) eq '13'"},
        {"filter": models.Q(DateOfBirth__hour='13')}
    ),
    (
        {"$filter": "minute(DateOfBirth) eq '55'"},
        {"filter": models.Q(DateOfBirth__minute='55')}
    ),
    (
        {"$filter": "second(DateOfBirth) eq '55'"},
        {"filter": models.Q(DateOfBirth__second='55')}
    ),
    (
        {"$filter": "Name eq 'John' and (Age gt '65' or Age lt '11')"},
        {"filter": models.Q(Name='John') & (models.Q(Age__gt='65') | models.Q(Age__lt='11'))}
    ),
    (
        {"$filter": "length(Name) eq 5"},
        {"filter": models.Q(Name__length=5)}
    ),
    (
        {"$filter": "year(DateOfBirth) eq 1990"},
        {"filter": models.Q(DateOfBirth__year=1990)}
    ),
    (
        {"$filter": "month(DateOfBirth) eq 5"},
        {"filter": models.Q(DateOfBirth__month=5)}
    ),
    (
        {"$filter": "day(DateOfBirth) eq 31"},
        {"filter": models.Q(DateOfBirth__day=31)}
    ),
    (
        {"$filter": "hour(DateOfBirth) eq 13"},
        {"filter": models.Q(DateOfBirth__hour=13)}
    ),
    (
        {"$filter": "minute(DateOfBirth) eq 55"},
        {"filter": models.Q(DateOfBirth__minute=55)}
    ),
    (
        {"$filter": "second(DateOfBirth) eq 55"},
        {"filter": models.Q(DateOfBirth__second=55)}
    ),
    (
        {"$filter": "Name eq 'John' and (Age gt 65 or Age lt 11)"},
        {"filter": models.Q(Name='John') & (models.Q(Age__gt=65) | models.Q(Age__lt=11))}
    ),
    (
        {"$filter": "Name eq 'John' and (Age gt '65' or Age lt 11)"},
        {"filter": models.Q(Name='John') & (models.Q(Age__gt='65') | models.Q(Age__lt=11))}
    ),
    (
        {"$filter": "concat(filed_A, 'value_B')"},
        {"filter": functions.Concat(models.F('filed_A'), models.Value("value_B"))}
    ),
    (
        {"$filter": "concat('filed_A', 'value_B')"},
        {"filter": functions.Concat(models.Value('filed_A'), models.Value("value_B"))}
    ),
    (
        {"$filter": "concat(filed_A, value_B)"},
        {"filter": functions.Concat(models.F('filed_A'), models.F("value_B"))}
    ),
    (
        {"$filter": "concat(concat(filed_A, field_C), 'value_B')"},
        {
            "filter": functions.Concat(
                functions.Concat(models.F('filed_A'), models.F('field_C')), models.Value("value_B")
            )
        }
    ),
    (
        {"$filter": "concat('value_B', concat(filed_A, field_C))"},
        {
            "filter": functions.Concat(
                models.Value("value_B"),
                functions.Concat(models.F('filed_A'), models.F('field_C'))
            )
        }
    ),
    (
        {"$filter": "length(field)"},
        {"filter": "field__length"}
    ),
    (
        {"$filter": "length(field) gt 'City'"},
        {"filter": models.Q(field__length__gt='City')}
    ),
    (
        {"$filter": "Name eq null"},
        {"filter": models.Q(Name__isnull=True)}
    ),
    (
        {"$filter": "Name ne null"},
        {"filter": ~models.Q(Name__isnull=True)}
    ),
    (
        {"$filter": "concat('value_B', concat(filed_A, field_C)) eq 'Loss Angeles'"},
        {
            "annotate": {
                "annotated_value": functions.Concat(
                    models.Value("value_B"),
                    functions.Concat(models.F('filed_A'), models.F('field_C'))
                )
            },
            "filter": models.Q(annotated_value="Loss Angeles"),
            "defer": "annotated_value"
        }
    ),
    (
        {"$filter": "concat(filed_A, filed_B, 'value_B')"},
        {"filter": functions.Concat(models.F('filed_A'), models.F('filed_B'), models.Value("value_B"))}
    ),
    (
        {"$filter": "not(Name eq 'John')"},
        {"filter": ~models.Q(Name="John")}
    ),
    (
        {"$filter": "concat(concat(City,', '), Country) eq 'Berlin, Germany'"},
        {
            "annotate": {
                "annotated_value": functions.Concat(
                    functions.Concat(models.F('City'), models.Value(', ')),
                    models.F("Country")
                )
            },
            "filter": models.Q(annotated_value="Berlin, Germany"),
            "defer": "annotated_value"
        }
    ),
    (
        {"$filter": "tolower(CompanyName) eq 'alfreds futterkists'"},
        {"filter": models.Q(CompanyName__lower='alfreds futterkists')}
    ),
    (
        {"$filter": "toupper(CompanyName) eq 'ALFRED FUTERKISTS'"},
        {"filter": models.Q(CompanyName__upper='ALFRED FUTERKISTS')}
    ),
    (
        {"$filter": "trim(CompanyName) eq 'Alfred Futerkists'"},
        {"filter": models.Q(CompanyName__trim='Alfred Futerkists')}
    ),
    (
        {"$filter": "tolower(trim(CompanyName)) eq 'alfred futerkists'"},
        {"filter": models.Q(CompanyName__trim__lower='alfred futerkists')}
    ),
    (
        {"$filter": "toupper(trim(CompanyName)) eq 'ALFRED FUTERKISTS'"},
        {"filter": models.Q(CompanyName__trim__upper='ALFRED FUTERKISTS')}
    ),
    (
        {"$filter": "trim(toupper(CompanyName)) eq 'ALFRED FUTERKISTS'"},
        {"filter": models.Q(CompanyName__upper__trim='ALFRED FUTERKISTS')}
    ),
    (
        {"$filter": "ceiling(Freight) eq 32"},
        {"filter": models.Q(Freight__ceil=32)}
    ),
    (
        {"$filter": "floor(Freight) eq 32"},
        {"filter": models.Q(Freight__floor=32)}
    ),
    (
        {"$filter": "round(Freight) eq 32"},
        {"filter": models.Q(Freight__round=32)}
    ),
    (
        {"$filter": "Price add 2.45 eq 5.00"},
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=5.0),
            "annotate": {"annotated_value": models.F("Price") + 2.45}
        }
    ),
    (
        {"$filter": "Price sub 0.55 eq 2.00"},
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=2.0),
            "annotate": {"annotated_value": models.F("Price") - 0.55}
        }
    ),
    (
        {"$filter": "Price mul 2.0 eq 5.10"},
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=5.10),
            "annotate": {"annotated_value": models.F("Price") * 2.0}
        }
    ),
    (
        {"$filter": "Price div 2.55 eq 1"},
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=1),
            "annotate": {"annotated_value": models.F("Price") / 2.55}
        }
    ),
    (
        {"$filter": "Rating div 2 eq 2"},
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=2),
            "annotate": {"annotated_value": models.F("Rating") / 2}
        }
    ),
    (
        {"$filter": "Rating div 2 eq 2.5"},
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=2.5),
            "annotate": {"annotated_value": models.F("Rating") / 2}
        }
    ),
    (
        {"$filter": "Rating mod 5 eq 0"},
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=0),
            "annotate": {"annotated_value": models.F("Rating") % 5}
        }
    ),
]
ORDER_TESTS = [
    (
        {"$orderby": "Name desc,LastName desc"},
        {"order_by": ["-Name", "-LastName"]}
    ),
    (
        {"$orderby": "Name asc,LastName desc"},
        {"order_by": ["Name", "-LastName"]}
    ),
    (
        {"$orderby": "Name ,LastName"},
        {"order_by": ["Name", "LastName"]}
    ),
]
SELECT_TEST = [
    (
        {"$select": "Name/company, LastName"},
        {"values": ["Name__company", "LastName"]}
    ),
    (
        {"$select": "Name, LastName"},
        {"values": ["Name", "LastName"]}
    ),
]
TOP_SKIP_TESTS = [
    (
        {"$top": "100"},
        {"__getitem__": slice(None, 100)}
    ),
    (
        {"$top": "100", "$skip": "50"},
        {"__getitem__": slice(50, 150)}
    ),
]


class OdataTest(TestCase):
    def test_filter(self):
        for t in FILTER_TESTS:
            result = django_params(t[0])
            self.assertEqual(result, t[1], msg=t[0])

    def test_order(self):
        for t in ORDER_TESTS:
            result = django_params(t[0])
            self.assertEqual(result, t[1], msg=t[0])

    def test_select(self):
        for t in SELECT_TEST:
            result = django_params(t[0])
            self.assertEqual(result, t[1], msg=t[0])

    def test_top_skip(self):
        for t in TOP_SKIP_TESTS:
            result = django_params(t[0])
            self.assertEqual(result, t[1], msg=t[0])


# indexof   # TODO need to implement this function
# replace   # TODO need to implement this function
# substring # TODO need to implement this function
# mod, sqrt, power
