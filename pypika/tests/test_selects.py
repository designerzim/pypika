# coding: utf8
import unittest

from pypika import Query, Table, Tables, Field as F, Case, functions as fn, Order, JoinType

__author__ = "Timothy Heys"
__email__ = "theys@kayak.com"


class SelectTests(unittest.TestCase):
    t = Table('abc')

    def test_empty_query(self):
        q = Query.from_('abc')

        self.assertEqual('', str(q))

    def test_select__star(self):
        q = Query.from_('abc').select('*')

        self.assertEqual('SELECT * FROM "abc"', str(q))

    def test_select__table_schema(self):
        q = Query.from_(Table('abc', 'schema1')).select('*')

        self.assertEqual('SELECT * FROM "schema1"."abc"', str(q))

    def test_select__star__replacement(self):
        q = Query.from_('abc').select('foo').select('*')

        self.assertEqual('SELECT * FROM "abc"', str(q))

    def test_select__distinct__single(self):
        q = Query.from_('abc').select('foo').distinct()

        self.assertEqual('SELECT distinct "foo" FROM "abc"', str(q))

    def test_select__distinct__multi(self):
        q = Query.from_('abc').select('foo', 'bar').distinct()

        self.assertEqual('SELECT distinct "foo","bar" FROM "abc"', str(q))

    def test_select__column__single__str(self):
        q = Query.from_('abc').select('foo')

        self.assertEqual('SELECT "foo" FROM "abc"', str(q))

    def test_select__column__single__field(self):
        t = Table('abc')
        q = Query.from_(t).select(t.foo)

        self.assertEqual('SELECT "foo" FROM "abc"', str(q))

    def test_select__columns__multi__str(self):
        q1 = Query.from_('abc').select('foo', 'bar')
        q2 = Query.from_('abc').select('foo').select('bar')

        self.assertEqual('SELECT "foo","bar" FROM "abc"', str(q1))
        self.assertEqual('SELECT "foo","bar" FROM "abc"', str(q2))

    def test_select__columns__multi__field(self):
        q1 = Query.from_(self.t).select(self.t.foo, self.t.bar)
        q2 = Query.from_(self.t).select(self.t.foo).select(self.t.bar)

        self.assertEqual('SELECT "foo","bar" FROM "abc"', str(q1))
        self.assertEqual('SELECT "foo","bar" FROM "abc"', str(q2))

    def test_select__fields_after_star(self):
        q = Query.from_('abc').select('*').select('foo')

        self.assertEqual('SELECT * FROM "abc"', str(q))

    def test_select__no_table(self):
        q = Query.select(1, 2, 3)

        self.assertEqual('SELECT 1,2,3', str(q))

    def test_select_then_add_table(self):
        q = Query.select(1).select(2, 3).from_('abc').select('foo')

        self.assertEqual('SELECT 1,2,3,"foo" FROM "abc"', str(q))

    def test_static_from_function_removed_after_called(self):
        with self.assertRaises(AttributeError):
            Query.from_('abc').from_('efg')

    def test_instance_from_function_removed_after_called(self):
        with self.assertRaises(AttributeError):
            Query.select(1).from_('abc').from_('efg')


class WhereTests(unittest.TestCase):
    t = Table('abc')

    def test_where_field_equals(self):
        q1 = Query.from_(self.t).select('*').where(self.t.foo == self.t.bar)
        q2 = Query.from_(self.t).select('*').where(self.t.foo.eq(self.t.bar))

        self.assertEqual('SELECT * FROM "abc" WHERE "foo"="bar"', str(q1))
        self.assertEqual('SELECT * FROM "abc" WHERE "foo"="bar"', str(q2))

    def test_where_field_equals_where(self):
        q = Query.from_(self.t).select('*').where(self.t.foo == 1).where(self.t.bar == self.t.baz)

        self.assertEqual('SELECT * FROM "abc" WHERE "foo"=1 AND "bar"="baz"', str(q))

    def test_where_field_equals_and(self):
        q = Query.from_(self.t).select('*').where((self.t.foo == 1) & (self.t.bar == self.t.baz))

        self.assertEqual('SELECT * FROM "abc" WHERE "foo"=1 AND "bar"="baz"', str(q))

    def test_where_field_equals_or(self):
        q = Query.from_(self.t).select('*').where((self.t.foo == 1) | (self.t.bar == self.t.baz))

        self.assertEqual('SELECT * FROM "abc" WHERE "foo"=1 OR "bar"="baz"', str(q))

    def test_where_nested_conditions(self):
        q = Query.from_(self.t).select('*').where((self.t.foo == 1) | (self.t.bar == self.t.baz)).where(self.t.baz == 0)

        self.assertEqual('SELECT * FROM "abc" WHERE ("foo"=1 OR "bar"="baz") AND "baz"=0', str(q))

    def test_where_field_starts_with(self):
        q = Query.from_(self.t).select(self.t.star).where(self.t.foo.like('ab%'))

        self.assertEqual("SELECT * FROM \"abc\" WHERE \"foo\" LIKE 'ab%'", str(q))

    def test_where_field_contains(self):
        q = Query.from_(self.t).select(self.t.star).where(self.t.foo.like('%fg%'))

        self.assertEqual("SELECT * FROM \"abc\" WHERE \"foo\" LIKE '%fg%'", str(q))

    def test_where_field_ends_with(self):
        q = Query.from_(self.t).select(self.t.star).where(self.t.foo.like('%yz'))

        self.assertEqual("SELECT * FROM \"abc\" WHERE \"foo\" LIKE '%yz'", str(q))

    def test_where_field_is_n_chars_long(self):
        q = Query.from_(self.t).select(self.t.star).where(self.t.foo.like('___'))

        self.assertEqual("SELECT * FROM \"abc\" WHERE \"foo\" LIKE '___'", str(q))

    def test_where_field_matches_regex(self):
        q = Query.from_(self.t).select(self.t.star).where(self.t.foo.regex(r'^b'))

        self.assertEqual("SELECT * FROM \"abc\" WHERE \"foo\" REGEX '^b'", str(q))


class GroupByTests(unittest.TestCase):
    t = Table('abc')

    def test_groupby__single(self):
        q = Query.from_(self.t).groupby(self.t.foo).select(self.t.foo)

        self.assertEqual('SELECT "foo" FROM "abc" GROUP BY "foo"', str(q))

    def test_groupby__multi(self):
        q = Query.from_(self.t).groupby(self.t.foo, self.t.bar).select(self.t.foo, self.t.bar)

        self.assertEqual('SELECT "foo","bar" FROM "abc" GROUP BY "foo","bar"', str(q))

    def test_groupby__count_star(self):
        q = Query.from_(self.t).groupby(self.t.foo).select(self.t.foo, fn.Count('*'))

        self.assertEqual('SELECT "foo",COUNT(*) FROM "abc" GROUP BY "foo"', str(q))

    def test_groupby__count_field(self):
        q = Query.from_(self.t).groupby(self.t.foo).select(self.t.foo, fn.Count(self.t.bar))

        self.assertEqual('SELECT "foo",COUNT("bar") FROM "abc" GROUP BY "foo"', str(q))

    def test_groupby__count_distinct(self):
        q = Query.from_(self.t).groupby(self.t.foo).select(self.t.foo, fn.Count('*').distinct())

        self.assertEqual('SELECT "foo",COUNT(DISTINCT *) FROM "abc" GROUP BY "foo"', str(q))

    def test_groupby__str(self):
        q = Query.from_('abc').groupby('foo').select('foo', fn.Count('*').distinct())

        self.assertEqual('SELECT "foo",COUNT(DISTINCT *) FROM "abc" GROUP BY "foo"', str(q))


class HavingTests(unittest.TestCase):
    t0, t1 = Tables('abc', 'efg')

    def test_having_greater_than(self):
        q = Query.from_(self.t0).select(
            self.t0.foo, fn.Sum(self.t0.bar)
        ).groupby(
            self.t0.foo
        ).having(
            fn.Sum(self.t0.bar) > 1
        )

        self.assertEqual('SELECT "foo",SUM("bar") FROM "abc" GROUP BY "foo" HAVING SUM("bar")>1', str(q))

    def test_having_and(self):
        q = Query.from_(self.t0).select(
            self.t0.foo, fn.Sum(self.t0.bar)
        ).groupby(
            self.t0.foo
        ).having(
            (fn.Sum(self.t0.bar) > 1) & (fn.Sum(self.t0.bar) < 100)
        )

        self.assertEqual('SELECT "foo",SUM("bar") FROM "abc" GROUP BY "foo" HAVING SUM("bar")>1 AND SUM("bar")<100',
                         str(q))

    def test_having_join_and_equality(self):
        q = Query.from_(self.t0).join(
            self.t1, how=JoinType.inner
        ).on(
            self.t0.foo == self.t1.foo
        ).select(
            self.t0.foo, fn.Sum(self.t1.bar), self.t0.buz
        ).groupby(
            self.t0.foo
        ).having(
            self.t0.buz == 'fiz'
        ).having(
            fn.Sum(self.t1.bar) > 100
        )

        self.assertEqual('SELECT "t0"."foo",SUM("t1"."bar"),"t0"."buz" FROM "abc" "t0" '
                         'INNER JOIN "efg" "t1" ON "t0"."foo"="t1"."foo" '
                         'GROUP BY "t0"."foo" '
                         "HAVING \"t0\".\"buz\"='fiz' AND SUM(\"t1\".\"bar\")>100", str(q))


class OrderByTests(unittest.TestCase):
    t = Table('abc')

    def test_orderby_single_field(self):
        q = Query.from_(self.t).orderby(self.t.foo).select(self.t.foo)

        self.assertEqual('SELECT "foo" FROM "abc" ORDER BY "foo"', str(q))

    def test_orderby_multi_fields(self):
        q = Query.from_(self.t).orderby(self.t.foo, self.t.bar).select(self.t.foo, self.t.bar)

        self.assertEqual('SELECT "foo","bar" FROM "abc" ORDER BY "foo","bar"', str(q))

    def test_orderby_single_str(self):
        q = Query.from_('abc').orderby('foo').select('foo')

        self.assertEqual('SELECT "foo" FROM "abc" ORDER BY "foo"', str(q))

    def test_orderby_asc(self):
        q = Query.from_(self.t).orderby(self.t.foo, order=Order.asc).select(self.t.foo)

        self.assertEqual('SELECT "foo" FROM "abc" ORDER BY "foo" ASC', str(q))

    def test_orderby_desc(self):
        q = Query.from_(self.t).orderby(self.t.foo, order=Order.desc).select(self.t.foo)

        self.assertEqual('SELECT "foo" FROM "abc" ORDER BY "foo" DESC', str(q))


class AliasTests(unittest.TestCase):
    t = Table('abc')

    def test_table_field(self):
        q = Query.from_(self.t).select(self.t.foo.as_('bar'))

        self.assertEqual('SELECT "foo" "bar" FROM "abc"', str(q))

    def test_table_field__multi(self):
        q = Query.from_(self.t).select(self.t.foo.as_('bar'), self.t.fiz.as_('buz'))

        self.assertEqual('SELECT "foo" "bar","fiz" "buz" FROM "abc"', str(q))

    def test_arithmetic_function(self):
        q = Query.from_(self.t).select((self.t.foo + self.t.bar).as_('biz'))

        self.assertEqual('SELECT "foo"+"bar" "biz" FROM "abc"', str(q))

    def test_functions_using_as(self):
        q = Query.from_(self.t).select(fn.Count('*').as_('foo'))

        self.assertEqual('SELECT COUNT(*) "foo" FROM "abc"', str(q))

    def test_functions_using_constructor_param(self):
        q = Query.from_(self.t).select(fn.Count('*', alias='foo'))

        self.assertEqual('SELECT COUNT(*) "foo" FROM "abc"', str(q))

    def test_ignored_in_where(self):
        q = Query.from_(self.t).select(self.t.foo).where(self.t.foo.as_('bar') == 1)

        self.assertEqual('SELECT "foo" FROM "abc" WHERE "foo"=1', str(q))

    def test_ignored_in_groupby(self):
        q = Query.from_(self.t).select(self.t.foo).groupby(self.t.foo.as_('bar'))

        self.assertEqual('SELECT "foo" FROM "abc" GROUP BY "foo"', str(q))

    def test_ignored_in_orderby(self):
        q = Query.from_(self.t).select(self.t.foo).orderby(self.t.foo.as_('bar'))

        self.assertEqual('SELECT "foo" FROM "abc" ORDER BY "foo"', str(q))

    def test_ignored_in_criterion(self):
        c = self.t.foo.as_('bar') == 1

        self.assertEqual('"foo"=1', str(c))

    def test_ignored_in_criterion_comparison(self):
        c = self.t.foo.as_('bar') == self.t.fiz.as_('buz')

        self.assertEqual('"foo"="fiz"', str(c))

    def test_ignored_in_field_inside_case(self):
        q = Query.from_(self.t).select(Case().when(self.t.foo == 1, 'a').else_(self.t.bar.as_('"buz"')))

        self.assertEqual("SELECT CASE WHEN \"foo\"=1 THEN 'a' ELSE \"bar\" END FROM \"abc\"", str(q))

    def test_case_using_as(self):
        q = Query.from_(self.t).select(Case().when(self.t.foo == 1, 'a').else_('b').as_('bar'))

        self.assertEqual("SELECT CASE WHEN \"foo\"=1 THEN 'a' ELSE 'b' END \"bar\" FROM \"abc\"", str(q))

    def test_case_using_constructor_param(self):
        q = Query.from_(self.t).select(Case(alias='bar').when(self.t.foo == 1, 'a').else_('b'))

        self.assertEqual("SELECT CASE WHEN \"foo\"=1 THEN 'a' ELSE 'b' END \"bar\" FROM \"abc\"", str(q))

    def test_select_aliases(self):
        test_query = Query.from_(self.t).select(
            self.t.foo.as_('fiz1'), self.t.bar.as_('buz1')
        ).groupby(
            self.t.foo.as_('fiz2'), self.t.bar.as_('buz2')
        )

        self.assertListEqual(['fiz1', 'buz1'], test_query.select_aliases())

    def test_select_aliases_mixed_with_fields(self):
        test_query = Query.from_(self.t).select(
            self.t.foo.as_('fiz1'), self.t.bar
        ).groupby(
            self.t.foo, self.t.bar.as_('buz2')
        )

        self.assertListEqual(['fiz1', 'bar'], test_query.select_aliases())

    def test_select_aliases_mixed_with_complex_fields(self):
        test_query = Query.from_(self.t).select(
            self.t.foo.as_('foobar'), fn.Count(self.t.fiz + self.t.buz)
        ).groupby(
            self.t.foo
        )

        self.assertListEqual(['foobar', 'COUNT("fiz"+"buz")'], test_query.select_aliases())

    def test_groupby_aliases(self):
        test_query = Query.from_(self.t).select(
            self.t.foo.as_('fiz1'), self.t.bar.as_('buz1')
        ).groupby(
            self.t.foo.as_('fiz2'), self.t.bar.as_('buz2')
        )

        self.assertListEqual(['fiz2', 'buz2'], test_query.groupby_aliases())

    def test_groupby_aliases_mixed_with_fields(self):
        test_query = Query.from_(self.t).select(
            self.t.foo.as_('fiz1'), self.t.bar
        ).groupby(
            self.t.foo, self.t.bar.as_('buz2')
        )

        self.assertListEqual(['foo', 'buz2'], test_query.groupby_aliases())


class SubqueryTests(unittest.TestCase):
    maxDiff = None

    table_abc, table_efg, table_hij = Tables('abc', 'efg', 'hij')

    def test_where__in(self):
        q = Query.from_(self.table_abc).select('*').where(self.table_abc.foo.isin(
            Query.from_(self.table_efg).select(self.table_efg.foo).where(self.table_efg.bar == 0)
        ))

        self.assertEqual('SELECT * FROM "abc" WHERE "foo" IN (SELECT "foo" FROM "efg" WHERE "bar"=0)', str(q))

    def test_join(self):
        subquery = Query.from_('efg').select('fiz', 'buz').where(F('buz') == 0)

        q = Query.from_(self.table_abc).join(subquery).on(
            self.table_abc.bar == subquery.buz
        ).select(self.table_abc.foo, subquery.fiz)

        self.assertEqual('SELECT "t0"."foo","t1"."fiz" FROM "abc" "t0" '
                         'JOIN (SELECT "fiz","buz" FROM "efg" WHERE "buz"=0) "t1" '
                         'ON "t0"."bar"="t1"."buz"', str(q))

    def test_where__equality(self):
        subquery = Query.from_('efg').select('fiz').where(F('buz') == 0)
        query = Query.from_(self.table_abc).select(
            self.table_abc.foo,
            self.table_abc.bar
        ).where(self.table_abc.bar == subquery)

        self.assertEqual('SELECT "foo","bar" FROM "abc" '
                         'WHERE "bar"=(SELECT "fiz" FROM "efg" WHERE "buz"=0)', str(query))

    def test_select_from_nested_query(self):
        subquery = Query.from_(self.table_abc).select(
            self.table_abc.foo,
            self.table_abc.bar,
            (self.table_abc.fizz + self.table_abc.buzz).as_('fizzbuzz'),
        )

        query = Query.from_(subquery).select(subquery.foo, subquery.bar, subquery.fizzbuzz)

        self.assertEqual('SELECT "foo","bar","fizzbuzz" '
                         'FROM ('
                         'SELECT "foo","bar","fizz"+"buzz" "fizzbuzz" '
                         'FROM "abc"'
                         ')', str(query))

    def test_select_from_nested_query_with_join(self):
        subquery1 = Query.from_(self.table_abc).select(
            self.table_abc.foo,
            fn.Sum(self.table_abc.fizz + self.table_abc.buzz).as_('fizzbuzz'),
        ).groupby(
            self.table_abc.foo
        )

        subquery2 = Query.from_(self.table_efg).select(
            self.table_efg.foo.as_('foo_two'),
            self.table_efg.bar,
        )

        query = Query.from_(subquery1).select(
            subquery1.foo, subquery1.fizzbuzz
        ).join(subquery2).on(subquery1.foo == subquery2.foo_two).select(
            subquery2.foo_two, subquery2.bar
        )

        self.assertEqual('SELECT '
                         '"t0"."foo","t0"."fizzbuzz",'
                         '"t1"."foo_two","t1"."bar" '
                         'FROM ('
                         'SELECT '
                         '"foo",SUM("fizz"+"buzz") "fizzbuzz" '
                         'FROM "abc" '
                         'GROUP BY "foo"'
                         ') "t0" JOIN ('
                         'SELECT '
                         '"foo" "foo_two","bar" '
                         'FROM "efg"'
                         ') "t1" ON "t0"."foo"="t1"."foo_two"', str(query))
