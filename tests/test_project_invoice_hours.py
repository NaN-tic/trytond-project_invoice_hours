#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import doctest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_depends, doctest_dropdb


class ProjectInvoiceHoursTestCase(unittest.TestCase):
    'Test Project Invoice Hours module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('project_invoice_hours')

    def test0006depends(self):
        'Test depends'
        test_depends()


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            ProjectInvoiceHoursTestCase))
    suite.addTests(doctest.DocFileSuite('scenario_project_invoice_hours.rst',
            setUp=doctest_dropdb, tearDown=doctest_dropdb, encoding='utf-8',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite
