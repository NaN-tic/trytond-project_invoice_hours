# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.pool import Pool, PoolMeta


class Work(metaclass=PoolMeta):
    __name__ = 'project.work'

    @classmethod
    def __setup__(cls):
        super(Work, cls).__setup__()

        # Add hours to project_invoice_method
        item = ('hours', 'On Hours')
        if item not in cls.project_invoice_method.selection:
            cls.project_invoice_method.selection.append(item)

    @classmethod
    def _get_quantity_to_invoice_hours(cls, works):
        quantities = cls._get_quantity_to_invoice_timesheet(works)
        for work_id, hours in quantities.items():
            work = cls(work_id)
            if (work.status and work.status.progress != 1) or work.invoice_line:
                quantities[work_id] = 0.0
        return quantities

    @classmethod
    def _get_invoiced_amount_hours(cls, works):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')
        Currency = pool.get('currency.currency')

        invoice_lines = InvoiceLine.browse([
                w.invoice_line.id for w in works
                if w.invoice_line])

        id2invoice_lines = dict((l.id, l) for l in invoice_lines)
        amounts = {}
        for work in works:
            currency = work.company.currency
            if work.invoice_line:
                invoice_line = id2invoice_lines[work.invoice_line.id]
                invoice_currency = (invoice_line.invoice.currency
                    if invoice_line.invoice else invoice_line.currency)
                amounts[work.id] = Currency.compute(invoice_currency,
                    invoice_line.amount, currency)
            else:
                amounts[work.id] = Decimal(0)
        return amounts

    def get_origins_to_invoice(self):
        origins = super().get_origins_to_invoice()
        if self.invoice_method == 'hours':
            origins.append(self)
        return origins
