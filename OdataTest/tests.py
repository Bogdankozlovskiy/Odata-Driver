from django.test import TestCase
from django.db import models
from django.db.models import functions
from urllib.parse import quote, parse_qs
from OdataTest.odata import django_params


FILTER_TESTS = [
    (
        "$filter=" + quote("foo eq '1'"),
        models.Q(foo='1')
    ),
    (
        "$filter=" + quote("foo eq 1"),
        models.Q(foo=1)
    ),
    (
        "$filter=" + quote("Address/City ne 'London'"),
        ~models.Q(Address__City='London')
    ),
    (
        "$filter=" + quote("start_date gt '2017-03-01'"),
        models.Q(start_date__gt='2017-03-01')
    ),
    (
        "$filter=" + quote("Price lt '20'"),
        models.Q(Price__lt='20')
    ),
    (
        "$filter=" + quote("Price lt 20"),
        models.Q(Price__lt=20)
    ),
    (
        "$filter=" + quote("Price le '100'"),
        models.Q(Price__lte='100')
    ),
    (
        "$filter=" + quote("Price le 100"),
        models.Q(Price__lte=100)
    ),
    (
        "$filter=" + quote("start_date ge '2017-03-01' and start_date lt '2017-03-02'"),
        models.Q(start_date__gte='2017-03-01') & models.Q(start_date__lt='2017-03-02')
    ),
    (
        "$filter=" + quote("location/postal_code eq '22980'"),
        models.Q(location__postal_code='22980')
    ),
    (
        "$filter=" + quote("location/postal_code eq 22980"),
        models.Q(location__postal_code=22980)
    ),
    (
        "$filter=" + quote("contains(name, 'Sessions') or contains(name, 'DeVos')"),
        models.Q(name__contains="Sessions") | models.Q(name__contains="DeVos")
    ),
    (
        "$filter=" + quote("location/postal_code eq '22980' and (contains(name, 'Sess') or contains(name, 'DeVos'))"),
        models.Q(location__postal_code='22980') & (models.Q(name__contains="Sess") | models.Q(name__contains="DeVos"))
    ),
    (
        "$filter=" + quote("location/postal_code eq 22980 and (contains(name, 'Sess') or contains(name, 'DeVos'))"),
        models.Q(location__postal_code=22980) & (models.Q(name__contains="Sess") | models.Q(name__contains="DeVos"))
    ),
    (
        "$filter=" + quote("(contains(name, 'Sess') or contains(name, 'DeVos')) and location/postal_code eq '22980'"),
        (models.Q(name__contains="Sess") | models.Q(name__contains="DeVos")) & models.Q(location__postal_code="22980")
    ),
    (
        "$filter=" + quote("(contains(name, 'Sess') or contains(name, 'DeVos')) and location/postal_code eq 22980"),
        (models.Q(name__contains="Sess") | models.Q(name__contains="DeVos")) & models.Q(location__postal_code=22980)
    ),
    (
        "$filter=" + quote("not contains(name, 'Sessions')"),
        ~models.Q(name__contains="Sessions")
    ),
    (
        "$filter=" + quote("endswith(Description,'milk')"),
        models.Q(Description__endswith="milk")
    ),
    (
        "$filter=" + quote("not endswith(Description,'milk')"),
        ~models.Q(Description__endswith="milk")
    ),
    (
        "$filter=" + quote("substringof(name, 'Sessions') or substringof(name, 'DeVos')"),
        models.Q(name__contains="Sessions") | models.Q(name__contains="DeVos")
    ),
    (
        "$filter=" + quote("startswith(Description,'milk')"),
        models.Q(Description__startswith="milk")
    ),
    (
        "$filter=" + quote("length(Name) eq '5'"),
        models.Q(Name__length='5')
    ),
    (
        "$filter=" + quote("year(DateOfBirth) eq '1990'"),
        models.Q(DateOfBirth__year='1990')
    ),
    (
        "$filter=" + quote("month(DateOfBirth) eq '5'"),
        models.Q(DateOfBirth__month='5')
    ),
    (
        "$filter=" + quote("day(DateOfBirth) eq '31'"),
        models.Q(DateOfBirth__day='31')
    ),
    (
        "$filter=" + quote("hour(DateOfBirth) eq '13'"),
        models.Q(DateOfBirth__hour='13')
    ),
    (
        "$filter=" + quote("minute(DateOfBirth) eq '55'"),
        models.Q(DateOfBirth__minute='55')
    ),
    (
        "$filter=" + quote("second(DateOfBirth) eq '55'"),
        models.Q(DateOfBirth__second='55')
    ),
    (
        "$filter=" + quote("Name eq 'John' and (Age gt '65' or Age lt '11')"),
        models.Q(Name='John') & (models.Q(Age__gt='65') | models.Q(Age__lt='11'))
    ),
    (
        "$filter=" + quote("length(Name) eq 5"),
        models.Q(Name__length=5)
    ),
    (
        "$filter=" + quote("year(DateOfBirth) eq 1990"),
        models.Q(DateOfBirth__year=1990)
    ),
    (
        "$filter=" + quote("month(DateOfBirth) eq 5"),
        models.Q(DateOfBirth__month=5)
    ),
    (
        "$filter=" + quote("day(DateOfBirth) eq 31"),
        models.Q(DateOfBirth__day=31)
    ),
    (
        "$filter=" + quote("hour(DateOfBirth) eq 13"),
        models.Q(DateOfBirth__hour=13)
    ),
    (
        "$filter=" + quote("minute(DateOfBirth) eq 55"),
        models.Q(DateOfBirth__minute=55)
    ),
    (
        "$filter=" + quote("second(DateOfBirth) eq 55"),
        models.Q(DateOfBirth__second=55)
    ),
    (
        "$filter=" + quote("Name eq 'John' and (Age gt 65 or Age lt 11)"),
        models.Q(Name='John') & (models.Q(Age__gt=65) | models.Q(Age__lt=11))
    ),
    (
        "$filter=" + quote("Name eq 'John' and (Age gt '65' or Age lt 11)"),
        models.Q(Name='John') & (models.Q(Age__gt='65') | models.Q(Age__lt=11))
    ),
    (
        "$filter=" + quote("concat(filed_A, 'value_B')"),
        functions.Concat(models.F('filed_A'), models.Value("value_B"))
    ),
    (
        "$filter=" + quote("concat('filed_A', 'value_B')"),
        functions.Concat(models.Value('filed_A'), models.Value("value_B"))
    ),
    (
        "$filter=" + quote("concat(filed_A, value_B)"),
        functions.Concat(models.F('filed_A'), models.F("value_B"))
    ),
    (
        "$filter=" + quote("concat(concat(filed_A, field_C), 'value_B')"),
        functions.Concat(functions.Concat(models.F('filed_A'), models.F('field_C')), models.Value("value_B"))
    ),
    (
        "$filter=" + quote("concat('value_B', concat(filed_A, field_C))"),
        functions.Concat(models.Value("value_B"), functions.Concat(models.F('filed_A'), models.F('field_C')))
    ),
    (
        "$filter=" + quote("length(field)"),
        "field__length"
    ),
    (
        "$filter=" + quote("length(field) gt 'City'"),
        models.Q(field__length__gt='City')
    ),
    (
        "$filter=" + quote("Name eq null"),
        models.Q(Name__isnull=True)
    ),
    (
        "$filter=" + quote("Name ne null"),
        ~models.Q(Name__isnull=True)
    ),
    # (
    #     "$filter=" + quote("concat('value_B', concat(filed_A, field_C)) eq 'Loss Angeles'"),
    #     functions.Concat(models.Value("value_B"), functions.Concat(models.F('filed_A'), models.F('field_C')))
    # ),
]
ORDER_TESTS = [
    (
        "$orderby=" + quote("Name desc,LastName desc"),
        ["-Name", "-LastName"]
    ),
    (
        "$orderby=" + quote("Name asc,LastName desc"),
        ["Name", "-LastName"]
    ),
    (
        "$orderby=" + quote("Name ,LastName"),
        ["Name", "LastName"]
    ),
]
SELECT_TEST = [
    (
        "$select=" + quote("Name/company, LastName"),
        ["Name__company", "LastName"]
    ),
    (
        "$select=" + quote("Name, LastName"),
        ["Name", "LastName"]
    ),
]
TOP_TESTS = [
    ("$top=100", slice(None, 100)),
    ("$top=50", slice(None, 50)),
]
SKIP_TESTS = [
    ("$skip=100", slice(100, None)),
    ("$skip=50", slice(50, None)),
]


class OdataTest(TestCase):
    def test_filter(self):
        for t in FILTER_TESTS:
            param_dict = parse_qs(t[0])
            result = django_params(param_dict)['filter']
            self.assertEqual(result.__str__(), t[1].__str__(), msg=param_dict)

    def test_order(self):
        for t in ORDER_TESTS:
            param_dict = parse_qs(t[0])
            result = django_params(param_dict)['orderby']
            self.assertEqual(result, t[1], msg=t[0])

    def test_select(self):
        for t in SELECT_TEST:
            param_dict = parse_qs(t[0])
            result = django_params(param_dict)['select']
            self.assertEqual(result, t[1], msg=t[0])

    def test_top(self):
        for t in TOP_TESTS:
            param_dict = parse_qs(t[0])
            result = django_params(param_dict)['top']
            self.assertEqual(result, t[1], msg=t[0])

    def test_skip(self):
        for t in SKIP_TESTS:
            param_dict = parse_qs(t[0])
            result = django_params(param_dict)['skip']
            self.assertEqual(result, t[1], msg=t[0])
