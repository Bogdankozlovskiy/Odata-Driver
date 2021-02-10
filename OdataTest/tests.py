from django.test import TestCase
from django.db import models
from django.db.models import functions
from urllib.parse import quote, parse_qs
from OdataTest.odata import django_params


FILTER_TESTS = [
    (
        "$filter=" + quote("foo eq '1'"),
        {"filter": models.Q(foo='1')}
    ),
    (
        "$filter=" + quote("foo eq 1"),
        {"filter": models.Q(foo=1)}
    ),
    (
        "$filter=" + quote("Address/City ne 'London'"),
        {"filter": ~models.Q(Address__City='London')}
    ),
    (
        "$filter=" + quote("start_date gt '2017-03-01'"),
        {"filter": models.Q(start_date__gt='2017-03-01')}
    ),
    (
        "$filter=" + quote("Price lt '20'"),
        {"filter": models.Q(Price__lt='20')}
    ),
    (
        "$filter=" + quote("Price lt 20"),
        {"filter": models.Q(Price__lt=20)}
    ),
    (
        "$filter=" + quote("Price le '100'"),
        {"filter": models.Q(Price__lte='100')}
    ),
    (
        "$filter=" + quote("Price le 100"),
        {"filter": models.Q(Price__lte=100)}
    ),
    (
        "$filter=" + quote("start_date ge '2017-03-01' and start_date lt '2017-03-02'"),
        {"filter": models.Q(start_date__gte='2017-03-01') & models.Q(start_date__lt='2017-03-02')}
    ),
    (
        "$filter=" + quote("location/postal_code eq '22980'"),
        {"filter": models.Q(location__postal_code='22980')}
    ),
    (
        "$filter=" + quote("location/postal_code eq 22980"),
        {"filter": models.Q(location__postal_code=22980)}
    ),
    (
        "$filter=" + quote("contains(name, 'Sessions') or contains(name, 'DeVos')"),
        {"filter": models.Q(name__contains="Sessions") | models.Q(name__contains="DeVos")}
    ),
    (
        "$filter=" + quote(
            "location/postal_code eq '22980' and (contains(name, 'Session') or contains(name, 'DeVos'))"
        ),
        {
            "filter": models.Q(location__postal_code='22980') & (
                    models.Q(name__contains="Session") | models.Q(name__contains="DeVos"))
        }
    ),
    (
        "$filter=" + quote("location/postal_code eq 22980 and (contains(name, 'Session') or contains(name, 'DeVos'))"),
        {
            "filter": models.Q(location__postal_code=22980) & (
                    models.Q(name__contains="Session") | models.Q(name__contains="DeVos"))
        }
    ),
    (
        "$filter=" + quote(
            "(contains(name, 'Session') or contains(name, 'DeVos')) and location/postal_code eq '22980'"
        ),
        {
            "filter": (models.Q(name__contains="Session") | models.Q(name__contains="DeVos")) & models.Q(
                location__postal_code="22980")
        }
    ),
    (
        "$filter=" + quote("(contains(name, 'Sess') or contains(name, 'DeVos')) and location/postal_code eq 22980"),
        {
            "filter": (models.Q(name__contains="Sess") | models.Q(name__contains="DeVos")) & models.Q(
                location__postal_code=22980
            )
        }
    ),
    (
        "$filter=" + quote("not contains(name, 'Sessions')"),
        {"filter": ~models.Q(name__contains="Sessions")}
    ),
    (
        "$filter=" + quote("endswith(Description,'milk')"),
        {"filter": models.Q(Description__endswith="milk")}
    ),
    (
        "$filter=" + quote("not endswith(Description,'milk')"),
        {"filter": ~models.Q(Description__endswith="milk")}
    ),
    (
        "$filter=" + quote("substringof(name, 'Sessions') or substringof(name, 'DeVos')"),
        {"filter": models.Q(name__contains="Sessions") | models.Q(name__contains="DeVos")}
    ),
    (
        "$filter=" + quote("startswith(Description,'milk')"),
        {"filter": models.Q(Description__startswith="milk")}
    ),
    (
        "$filter=" + quote("length(Name) eq '5'"),
        {"filter": models.Q(Name__length='5')}
    ),
    (
        "$filter=" + quote("year(DateOfBirth) eq '1990'"),
        {"filter": models.Q(DateOfBirth__year='1990')}
    ),
    (
        "$filter=" + quote("month(DateOfBirth) eq '5'"),
        {"filter": models.Q(DateOfBirth__month='5')}
    ),
    (
        "$filter=" + quote("day(DateOfBirth) eq '31'"),
        {"filter": models.Q(DateOfBirth__day='31')}
    ),
    (
        "$filter=" + quote("hour(DateOfBirth) eq '13'"),
        {"filter": models.Q(DateOfBirth__hour='13')}
    ),
    (
        "$filter=" + quote("minute(DateOfBirth) eq '55'"),
        {"filter": models.Q(DateOfBirth__minute='55')}
    ),
    (
        "$filter=" + quote("second(DateOfBirth) eq '55'"),
        {"filter": models.Q(DateOfBirth__second='55')}
    ),
    (
        "$filter=" + quote("Name eq 'John' and (Age gt '65' or Age lt '11')"),
        {"filter": models.Q(Name='John') & (models.Q(Age__gt='65') | models.Q(Age__lt='11'))}
    ),
    (
        "$filter=" + quote("length(Name) eq 5"),
        {"filter": models.Q(Name__length=5)}
    ),
    (
        "$filter=" + quote("year(DateOfBirth) eq 1990"),
        {"filter": models.Q(DateOfBirth__year=1990)}
    ),
    (
        "$filter=" + quote("month(DateOfBirth) eq 5"),
        {"filter": models.Q(DateOfBirth__month=5)}
    ),
    (
        "$filter=" + quote("day(DateOfBirth) eq 31"),
        {"filter": models.Q(DateOfBirth__day=31)}
    ),
    (
        "$filter=" + quote("hour(DateOfBirth) eq 13"),
        {"filter": models.Q(DateOfBirth__hour=13)}
    ),
    (
        "$filter=" + quote("minute(DateOfBirth) eq 55"),
        {"filter": models.Q(DateOfBirth__minute=55)}
    ),
    (
        "$filter=" + quote("second(DateOfBirth) eq 55"),
        {"filter": models.Q(DateOfBirth__second=55)}
    ),
    (
        "$filter=" + quote("Name eq 'John' and (Age gt 65 or Age lt 11)"),
        {"filter": models.Q(Name='John') & (models.Q(Age__gt=65) | models.Q(Age__lt=11))}
    ),
    (
        "$filter=" + quote("Name eq 'John' and (Age gt '65' or Age lt 11)"),
        {"filter": models.Q(Name='John') & (models.Q(Age__gt='65') | models.Q(Age__lt=11))}
    ),
    (
        "$filter=" + quote("concat(filed_A, 'value_B')"),
        {"filter": functions.Concat(models.F('filed_A'), models.Value("value_B"))}
    ),
    (
        "$filter=" + quote("concat('filed_A', 'value_B')"),
        {"filter": functions.Concat(models.Value('filed_A'), models.Value("value_B"))}
    ),
    (
        "$filter=" + quote("concat(filed_A, value_B)"),
        {"filter": functions.Concat(models.F('filed_A'), models.F("value_B"))}
    ),
    (
        "$filter=" + quote("concat(concat(filed_A, field_C), 'value_B')"),
        {
            "filter": functions.Concat(
                functions.Concat(models.F('filed_A'), models.F('field_C')), models.Value("value_B")
            )
        }
    ),
    (
        "$filter=" + quote("concat('value_B', concat(filed_A, field_C))"),
        {
            "filter": functions.Concat(
                models.Value("value_B"),
                functions.Concat(models.F('filed_A'), models.F('field_C'))
            )
        }
    ),
    (
        "$filter=" + quote("length(field)"),
        {"filter": "field__length"}
    ),
    (
        "$filter=" + quote("length(field) gt 'City'"),
        {"filter": models.Q(field__length__gt='City')}
    ),
    (
        "$filter=" + quote("Name eq null"),
        {"filter": models.Q(Name__isnull=True)}
    ),
    (
        "$filter=" + quote("Name ne null"),
        {"filter": ~models.Q(Name__isnull=True)}
    ),
    (
        "$filter=" + quote("concat('value_B', concat(filed_A, field_C)) eq 'Loss Angeles'"),
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
        "$filter=" + quote("concat(filed_A, filed_B, 'value_B')"),
        {"filter": functions.Concat(models.F('filed_A'), models.F('filed_B'), models.Value("value_B"))}
    ),
    (
        "$filter=" + quote("not(Name eq 'John')"),
        {"filter": ~models.Q(Name="John")}
    ),
    (
        "$filter=" + quote("concat(concat(City,', '), Country) eq 'Berlin, Germany'"),
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
        "$filter=" + quote("tolower(CompanyName) eq 'alfreds futterkists'"),
        {"filter": models.Q(CompanyName__lower='alfreds futterkists')}
    ),
    (
        "$filter=" + quote("toupper(CompanyName) eq 'ALFRED FUTERKISTS'"),
        {"filter": models.Q(CompanyName__upper='ALFRED FUTERKISTS')}
    ),
    (
        "$filter=" + quote("trim(CompanyName) eq 'Alfred Futerkists'"),
        {"filter": models.Q(CompanyName__trim='Alfred Futerkists')}
    ),
    (
        "$filter=" + quote("tolower(trim(CompanyName)) eq 'alfred futerkists'"),
        {"filter": models.Q(CompanyName__trim__lower='alfred futerkists')}
    ),
    (
        "$filter=" + quote("toupper(trim(CompanyName)) eq 'ALFRED FUTERKISTS'"),
        {"filter": models.Q(CompanyName__trim__upper='ALFRED FUTERKISTS')}
    ),
    (
        "$filter=" + quote("trim(toupper(CompanyName)) eq 'ALFRED FUTERKISTS'"),
        {"filter": models.Q(CompanyName__upper__trim='ALFRED FUTERKISTS')}
    ),
    (
        "$filter=" + quote("ceiling(Freight) eq 32"),
        {"filter": models.Q(Freight__ceil=32)}
    ),
    (
        "$filter=" + quote("floor(Freight) eq 32"),
        {"filter": models.Q(Freight__floor=32)}
    ),
    (
        "$filter=" + quote("round(Freight) eq 32"),
        {"filter": models.Q(Freight__round=32)}
    ),
    (
        "$filter=" + quote("Price add 2.45 eq 5.00"),
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=5.0),
            "annotate": {"annotated_value": models.F("Price") + 2.45}
        }
    ),
    (
        "$filter=" + quote("Price sub 0.55 eq 2.00"),
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=2.0),
            "annotate": {"annotated_value": models.F("Price") - 0.55}
        }
    ),
    (
        "$filter=" + quote("Price mul 2.0 eq 5.10"),
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=5.10),
            "annotate": {"annotated_value": models.F("Price") * 2.0}
        }
    ),
    (
        "$filter=" + quote("Price div 2.55 eq 1"),
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=1),
            "annotate": {"annotated_value": models.F("Price") / 2.55}
        }
    ),
    (
        "$filter=" + quote("Rating div 2 eq 2"),
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=2),
            "annotate": {"annotated_value": models.F("Rating") / 2}
        }
    ),
    (
        "$filter=" + quote("Rating div 2 eq 2.5"),
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=2.5),
            "annotate": {"annotated_value": models.F("Rating") / 2}
        }
    ),
    (
        "$filter=" + quote("Rating mod 5 eq 0"),
        {
            'defer': 'annotated_value',
            "filter": models.Q(annotated_value=0),
            "annotate": {"annotated_value": models.F("Rating") % 5}
        }
    ),
]
ORDER_TESTS = [
    (
        "$orderby=" + quote("Name desc,LastName desc"),
        {"orderby": ["-Name", "-LastName"]}
    ),
    (
        "$orderby=" + quote("Name asc,LastName desc"),
        {"orderby": ["Name", "-LastName"]}
    ),
    (
        "$orderby=" + quote("Name ,LastName"),
        {"orderby": ["Name", "LastName"]}
    ),
]
SELECT_TEST = [
    (
        "$select=" + quote("Name/company, LastName"),
        {"select": ["Name__company", "LastName"]}
    ),
    (
        "$select=" + quote("Name, LastName"),
        {"select": ["Name", "LastName"]}
    ),
]
TOP_TESTS = [
    ("$top=100", {"top": slice(None, 100)}),
    ("$top=50", {"top": slice(None, 50)}),
]
SKIP_TESTS = [
    ("$skip=100", {"skip": slice(100, None)}),
    ("$skip=50", {"skip": slice(50, None)}),
]
EXPAND_TEST = [
    (
        "$expand=" + quote("Products"),
        {"expand": ["Products"]}
    ),
    (
        "$expand=" + quote("Products/Suppliers"),
        {"expand": ["Products__Suppliers"]}
    ),
    (
        "$expand=" + quote("Category,Suppliers"),
        {"expand": ["Category", "Suppliers"]}
    ),
]


class OdataTest(TestCase):
    def test_filter(self):
        for t in FILTER_TESTS:
            param_dict = parse_qs(t[0])
            result = django_params(param_dict)
            self.assertEqual(result, t[1], msg=param_dict)

    def test_order(self):
        for t in ORDER_TESTS:
            param_dict = parse_qs(t[0])
            result = django_params(param_dict)
            self.assertEqual(result, t[1], msg=t[0])

    def test_select(self):
        for t in SELECT_TEST:
            param_dict = parse_qs(t[0])
            result = django_params(param_dict)
            self.assertEqual(result, t[1], msg=t[0])

    def test_top(self):
        for t in TOP_TESTS:
            param_dict = parse_qs(t[0])
            result = django_params(param_dict)
            self.assertEqual(result, t[1], msg=t[0])

    def test_skip(self):
        for t in SKIP_TESTS:
            param_dict = parse_qs(t[0])
            result = django_params(param_dict)
            self.assertEqual(result, t[1], msg=t[0])

    def test_expand(self):
        for t in EXPAND_TEST:
            param_dict = parse_qs(t[0])
            result = django_params(param_dict)
            self.assertEqual(result, t[1], msg=t[0])

# indexof   # TODO need to implement this function
# replace   # TODO need to implement this function
# substring # TODO need to implement this function
# mod, sqrt, power
