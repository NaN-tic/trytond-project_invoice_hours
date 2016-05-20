#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from datetime import timedelta
from decimal import Decimal
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['Work']


class Work:
    __metaclass__ = PoolMeta
    __name__ = 'project.work'

    @classmethod
    def __setup__(cls):
        super(Work, cls).__setup__()

        # Add hours to project_invoice_method
        item = ('hours', 'On Hours')
        if item not in cls.project_invoice_method.selection:
            cls.project_invoice_method.selection.append(item)

    @staticmethod
    def _get_invoiced_duration_hours(works):
        Work = Pool().get('project.work')
        # Needed to browse invoice lines
        with Transaction().set_user(0, set_context=True):
            works = Work.browse([x.id for x in works])
        return dict((w.id, timedelta(hours=w.invoice_line.quantity or 0.0))
            for w in works if w.invoice_line)

    @staticmethod
    def _get_duration_to_invoice_hours(works):
        return dict((w.id, w.effort_duration) for w in works
            if w.state == 'done' and not w.invoice_line)

    @staticmethod
    def _get_invoiced_amount_hours(works):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')

        with Transaction().set_user(0, set_context=True):
            invoice_lines = InvoiceLine.browse([
                    w.invoice_line.id for w in works
                    if w.invoice_line])

        id2invoice_lines = dict((l.id, l) for l in invoice_lines)
        amounts = {}
        for work in works:
            if work.invoice_line:
                invoice_line = id2invoice_lines[work.invoice_line.id]
                amounts[work.id] = invoice_line.amount
            else:
                amounts[work.id] = Decimal(0)
        return amounts

    def _get_lines_to_invoice_hours(self):
        if (not self.invoice_line and self.timesheet_duration
                and self.state == 'done'):
            if not self.product:
                self.raise_user_error('missing_product', (self.rec_name,))
            elif self.list_price is None:
                self.raise_user_error('missing_list_price', (self.rec_name,))
            return [{
                    'product': self.product,
                    'quantity': self.effort_hours,
                    'unit_price': self.list_price,
                    'origin': self,
                    'description': self.work.name,
                    }]
        return []
