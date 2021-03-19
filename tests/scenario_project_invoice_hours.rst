===============================
Project Invoice Effort Scenario
===============================

=============
General Setup
=============

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules, set_user
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_chart, \
    ...     get_accounts
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     create_payment_term
    >>> today = datetime.date.today()


Install project_invoice::

    >>> config = activate_modules('project_invoice_hours')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create project user::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> project_user = User()
    >>> project_user.name = 'Project'
    >>> project_user.login = 'project'
    >>> project_group, = Group.find([('name', '=', 'Project Administration')])
    >>> timesheet_group, = Group.find([('name', '=', 'Timesheet Administration')])
    >>> project_user.groups.extend([project_group, timesheet_group])
    >>> project_user.save()

Create project invoice user::

    >>> project_invoice_user = User()
    >>> project_invoice_user.name = 'Project Invoice'
    >>> project_invoice_user.login = 'project_invoice'
    >>> project_invoice_group, = Group.find([('name', '=', 'Project Invoice')])
    >>> project_group, = Group.find([('name', '=', 'Project Administration')])
    >>> project_invoice_user.groups.extend(
    ...     [project_invoice_group, project_group])
    >>> project_invoice_user.save()

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> revenue = accounts['revenue']

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Create customer::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.customer_payment_term = payment_term
    >>> customer.save()

Create employee::

    >>> Employee = Model.get('company.employee')
    >>> employee = Employee()
    >>> party = Party(name='Employee')
    >>> party.save()
    >>> employee.party = party
    >>> employee.company = company
    >>> employee.save()

Create account category::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_revenue = revenue
    >>> account_category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> hour, = ProductUom.find([('name', '=', 'Hour')])
    >>> Product = Model.get('product.product')
    >>> ProductTemplate = Model.get('product.template')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'Service'
    >>> template.default_uom = hour
    >>> template.type = 'service'
    >>> template.list_price = Decimal('20')
    >>> template.account_category = account_category
    >>> template.save()
    >>> product.template = template
    >>> product.save()

Create a Project::

    >>> set_user(project_user)
    >>> ProjectWork = Model.get('project.work')
    >>> project = ProjectWork()
    >>> project.name = 'Test effort'
    >>> project.type = 'project'
    >>> project.party = customer
    >>> project.project_invoice_method = 'hours'
    >>> project.product = product
    >>> project.timesheet_available = True
    >>> project.effort_duration = datetime.timedelta(hours=1)
    >>> task = ProjectWork()
    >>> task.name = 'Task 1'
    >>> task.type = 'task'
    >>> task.product = product
    >>> task.timesheet_available = True
    >>> task.effort_duration = datetime.timedelta(hours=3)
    >>> project.children.append(task)
    >>> project.save()
    >>> task, = project.children

Create timesheets::

    >>> TimesheetLine = Model.get('timesheet.line')
    >>> line = TimesheetLine()
    >>> line.employee = employee
    >>> line.duration = datetime.timedelta(hours=3)
    >>> line.work, = task.timesheet_works
    >>> line.save()
    >>> line = TimesheetLine()
    >>> line.employee = employee
    >>> line.duration = datetime.timedelta(hours=2)
    >>> line.work, = project.timesheet_works
    >>> line.save()

Check project hours::

    >>> project.reload()
    >>> project.invoiced_duration
    datetime.timedelta(0)
    >>> project.duration_to_invoice
    datetime.timedelta(0)
    >>> project.invoiced_amount
    Decimal('0.00')

Do 1 task::

    >>> task.state = 'done'
    >>> task.save()

Check project hours::

    >>> project.reload()
    >>> project.invoiced_duration
    datetime.timedelta(0)
    >>> project.duration_to_invoice == datetime.timedelta(seconds=10800)
    True
    >>> project.invoiced_amount
    Decimal('0.00')

Invoice project::

    >>> config.user = project_invoice_user.id
    >>> project.click('invoice')
    >>> project.invoiced_duration == datetime.timedelta(seconds=10800)
    True
    >>> project.duration_to_invoice
    datetime.timedelta(0)
    >>> project.invoiced_amount
    Decimal('60.00')
