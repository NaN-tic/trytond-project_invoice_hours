# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta

__all__ = ['Work']


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
    def _get_invoiced_duration_hours(cls, works):
        return cls._get_duration_timesheet(works, True)

    @classmethod
    def _get_duration_to_invoice_hours(cls, works):
        w = [x for x in works if x.state == 'done']
        return cls._get_duration_timesheet(w, False)

    @classmethod
    def _get_invoiced_amount_hours(cls, works):
        return cls._get_invoiced_amount_timesheet(works)

    def _get_lines_to_invoice_hours(self):
        if self.state == 'done':
            return self._get_lines_to_invoice_timesheet()
        else:
            return []
