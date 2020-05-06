from odoo import api, fields, models, exceptions
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"


    @api.multi
    def action_confirm(self):
        imediate_obj=self.env['stock.immediate.transfer']
        res=super(SaleOrder,self).action_confirm()
        for order in self:

            warehouse=order.warehouse_id
            if warehouse.is_delivery_set_to_done and order.picking_ids: 
                for picking in self.picking_ids:
                    picking.action_confirm()
                    picking.action_assign()


                    #imediate_rec = imediate_obj.create({'pick_ids': [(4, order.picking_ids.id)]})
                    #imediate_rec.process()
                    if picking.state !='done':
                        for move in picking.move_ids_without_package:
                            move.quantity_done = move.product_uom_qty
                        #picking.button_validate()

            #self._cr.commit()

        return res  


    @api.depends('effective_date')
    def creation_et_validation_facture(self):
        raise UserError(_('Avant le for'))
        for order in self:
            raise UserError(_('juste apres le for'))
            warehouse=order.warehouse_id
            raise UserError(_(warehouse))
            if warehouse.create_invoice and not order.invoice_ids:
                raise UserError(_('dans le 1er if'))
                order.action_invoice_create()  
            if warehouse.validate_invoice and order.invoice_ids:
                for invoice in order.invoice_ids:
                    invoice.action_invoice_open()
