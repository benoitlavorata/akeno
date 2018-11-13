# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.addons.aft_utils.models.tools import format_amount_to_integer

from dateutil import relativedelta

FORMAT_DATE = "%d/%m/%Y"
FORMAT_DATE2 = "%Y-%m-%d"

MOIS = [
    'Janvier',
    'Février',
    'Mars',
    'Avril',
    'Mai',
    'Juin',
    'Juillet',
    'Aout',
    'Septembre',
    'Octobre',
    'Novembre',
    'Décembre']


class ElementsRetenueReport(models.AbstractModel):

    _name = 'report.aft_paie.dipes_report'

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name(
            'aft_paie.dipes_report')

        # si le mois est choisi alors on ecrase la valeur de la periode
        by_month = data['form']['search_by_month']
        mois = int(data['form']['mois_de_paie'])
        filtrer = data['form']['filter_employees']

        if by_month and mois:
            oday = datetime.now()
            first_of_month = datetime.strptime(
                "1/%s/%s" % (str(mois), str(oday.year)),
                FORMAT_DATE)

            lastday = (first_of_month + relativedelta.relativedelta(
                months=+1,
                day=1,
                days=-1)).strftime(FORMAT_DATE2)

            day1 = first_of_month.strftime(FORMAT_DATE2)

            data['form']['date_to'] = lastday
            data['form']['date_from'] = day1

        # on recupere les data de la periode
        employee_ids = data['form']['employees']
        borne_max = data['form']['date_to']
        borne_min = data['form']['date_from']

        domain = []
        if borne_max and borne_min:
            domain.append(('date_to', '<=', borne_max))
            domain.append(('date_from', '>=', borne_min))

        if data['form']['lots']:
            domain.append(('payslip_run_id', 'in', data['form']['lots']))

        if filtrer and len(employee_ids) > 0:
            domain.append(('employee_id', 'in', employee_ids))

        records = self.env['hr.payslip'].search(domain)
        records = records.sorted(lambda x: x.employee_id.name)

        # calcule le nombre de jours
        debut = fields.Date.from_string(borne_min)
        fin = fields.Date.from_string(borne_max)
        nbj = (fin - debut).days

        paies = []
        totaux = {}
        to_brut = 0
        to_sbt = 0
        to_sc = 0
        to_irpp_men = 0
        to_at = 0
        to_af = 0
        to_pvid = 0

        to_total = 0

        for record in records:
            paie = {}
            ltotal = 0

            paie['name'] = record.employee_id.name

            for line in record.details_by_salary_rule_category:
                if line.code == 'GROSS':
                    paie['brut'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_brut += line.total
                elif line.code == 'SBT':
                    paie['sbt'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_sbt += line.total
                elif line.code == 'SC':
                    paie['sc'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_sc += line.total
                elif line.code == 'IRPP_MENSUEL':
                    paie['irpp'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_irpp_men += line.total
                elif line.code == 'AT':
                    paie['at'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_at += line.total
                elif line.code == 'AF':
                    paie['af'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_af += line.total
                elif line.code == 'PVID':
                    paie['pvid'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_pvid += line.total

            paie['ltotal'] = format_amount_to_integer(ltotal)
            to_total += ltotal
            paies.append(paie)

        totaux['brut'] = format_amount_to_integer(to_brut)
        totaux['sbt'] = format_amount_to_integer(to_sbt)
        totaux['sc'] = format_amount_to_integer(to_sc)
        totaux['irpp'] = format_amount_to_integer(to_irpp_men)
        totaux['at'] = format_amount_to_integer(to_at)
        totaux['af'] = format_amount_to_integer(to_af)
        totaux['pvid'] = format_amount_to_integer(to_pvid)
        totaux['nbj'] = nbj + 1
        totaux['debut'] = debut.strftime(FORMAT_DATE)
        totaux['fin'] = fin.strftime(FORMAT_DATE)

        if not totaux or not paies:
            raise Warning(u'Aucun bulletin de paie ne correspond\
                à votre recherche')

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'paies': paies,
            'totaux': totaux,
            'data': data['form']
        }

        return report_obj.render(
            'aft_paie.dipes_report',
            docargs)
