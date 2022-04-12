# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from collections import defaultdict
import datetime
import math
from sql import Null
from sql.aggregate import Sum
from trytond.tools import reduce_ids, grouped_slice

def round_time(seconds, round_minutes=5):
    round_seconds = round_minutes * 60
    return math.ceil(seconds / round_seconds) * round_seconds

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
            if work.invoice_line:
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

    @classmethod
    def _get_quantity_to_invoice_timesheet(cls, works):
        pool = Pool()
        TimesheetLine = pool.get('timesheet.line')
        cursor = Transaction().connection.cursor()
        line = TimesheetLine.__table__()

        upto2tworks = defaultdict(list)
        twork2work = {}
        for work in works:
            upto = work.invoice_timesheet_up_to
            for timesheet_work in work.timesheet_works:
                twork2work[timesheet_work.id] = work.id
                upto2tworks[upto].append(timesheet_work.id)

        durations = defaultdict(datetime.timedelta)
        query = line.select(
            line.work, Sum(line.duration),
            group_by=line.work)
        for upto, tworks in upto2tworks.items():
            for sub_ids in grouped_slice(tworks):
                query.where = (reduce_ids(line.work, sub_ids)
                    & (line.invoice_line == Null))
                if upto:
                    query.where &= (line.date <= upto)
                cursor.execute(*query)

                for twork_id, duration in cursor:
                    if duration:
                        # SQLite uses float for SUM
                        if not isinstance(duration, datetime.timedelta):
                            duration = datetime.timedelta(seconds=duration)
                        durations[twork2work[twork_id]] += duration

        quantities = {}
        for work in works:
            duration = durations[work.id]
            if work.list_price:
                duration = round_time(duration.total_seconds())
                hours = duration / 60 / 60
                if work.unit_to_invoice:
                    hours = work.unit_to_invoice.round(hours)
                quantities[work.id] = hours
        return quantities