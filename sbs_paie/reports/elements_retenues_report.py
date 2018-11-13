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

    _name = 'report.aft_paie.report_elements_retenues'

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name(
            'aft_paie.report_elements_retenues')

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
        to_sc = 0
        to_sni = 0
        to_irpp_men = 0
        to_cac = 0
        to_tdl = 0
        to_rav = 0
        to_cfc = 0
        to_cnps = 0
        to_retenues = 0

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
                elif line.code == 'SC':
                    paie['sc'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_sc += line.total
                elif line.code == 'SNI':
                    paie['sni'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_sni += line.total
                elif line.code == 'IRPP_MENSUEL':
                    paie['irpp'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_irpp_men += line.total
                elif line.code == 'CAC':
                    paie['cac'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_cac += line.total
                elif line.code == 'TDL':
                    paie['tdl'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_tdl += line.total
                elif line.code == 'RAV':
                    paie['rav'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_rav += line.total
                elif line.code == 'CFC':
                    paie['cfc'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_cfc += line.total
                elif line.code == 'CNPS':
                    paie['cnps'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_cnps += line.total
                elif line.code == 'RETENUES':
                    paie['retenues'] = format_amount_to_integer(line.total)
                    ltotal += line.total
                    to_retenues += line.total

            paie['ltotal'] = format_amount_to_integer(ltotal)
            to_total += ltotal
            paies.append(paie)

        totaux['brut'] = format_amount_to_integer(to_brut)
        totaux['sc'] = format_amount_to_integer(to_sc)
        totaux['sni'] = format_amount_to_integer(to_sni)
        totaux['irpp'] = format_amount_to_integer(to_irpp_men)
        totaux['cac'] = format_amount_to_integer(to_cac)
        totaux['tdl'] = format_amount_to_integer(to_tdl)
        totaux['rav'] = format_amount_to_integer(to_rav)
        totaux['cfc'] = format_amount_to_integer(to_cfc)
        totaux['cnps'] = format_amount_to_integer(to_cnps)
        totaux['retenues'] = format_amount_to_integer(to_retenues)
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
            'aft_paie.report_elements_retenues',
            docargs)
