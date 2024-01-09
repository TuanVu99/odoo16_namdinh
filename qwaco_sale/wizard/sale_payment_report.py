# -*- coding: utf-8 -*-

from datetime import timedelta, date, datetime
import base64

import os
from io import BytesIO
import openpyxl
from openpyxl.styles import NamedStyle, Font, Border, Side, Alignment
from openpyxl.writer.excel import save_virtual_workbook
from openpyxl.worksheet import filters
from odoo import api, fields, models


class StockListReport(models.TransientModel):
    _name = 'stock.list.report'
    _description = 'Báo cáo tồn kho vật tư'

    year = fields.Integer('Năm', required=True, default=fields.date.today().year)
    stock = fields.Many2one('stock.location', domain=[('usage', '=', 'internal')])
    is_order = fields.Boolean('Cần đặt hàng' , default=False)

    def action_report_stock(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        wb = openpyxl.load_workbook(dir_path + '%s..%stemplates%sstock_material_report.xlsx' % (os.sep, os.sep, os.sep))
        ws = wb['Sheet1']
        current_year = self.year
        stock = []
        if self.stock:
            stock.append(self.stock.id)
        else:
            rec = self.env['stock.location'].search([('usage', '=', 'internal')])
            print(rec)
            for r in rec:
                stock.append(r['id'])
        if self.is_order:
            sql ='''with dt(ma_sp,ma_hang,ten_sp,phan_loai,hang_sx,model,don_vi,don_gia,ton_dau_ky,nhap_trong_ky,xuat_trong_ky,nhap_tra_lai,kiem_ke_kho,ton_cuoi_ky,ton_kho_toi_thieu,ton_kho_toi_da,sl_thuc_te,slsd_t1,slsd_t2,slsd_t3,slsd_t4,slsd_t5,slsd_t6,slsd_t7,slsd_t8,slsd_t9,slsd_t10,slsd_t11,slsd_t12,gtsd_t1,gtsd_t2,gtsd_t3,gtsd_t4,gtsd_t5,gtsd_t6,gtsd_t7,gtsd_t8,gtsd_t9,gtsd_t10,gtsd_t11,gtsd_t12,gtsd_cac_nam_truoc,gt_ton_kho) as(
                   SELECT pp.id as ma_sp ,pt.default_code as ma_hang, pt.name as ten_sp, 
                       case when pt.x_supplies_type = 'supplies' then 'Vật tư tiêu chuẩn'
                        when pt.x_supplies_type = 'labor_protection' then 'Bảo hộ lao động'
                        when pt.x_supplies_type = 'stationery' then 'Văn phòng phẩm'
                        when pt.x_supplies_type = 'supplies_project' then 'Vật tư xuất cho dự án' end as phan_loai,
                       pt.x_product_company as hang_sx,
                       pt.x_code_brand as  model,
                       coalesce(it2.value,uu."name") as don_vi,
                       ip.value_float as don_gia,		 
                            sum(
                                case
                                when(sml.date::date < '{year}-01-01' and sl1.usage = 'internal') then -sml.qty_done
                                when(sml.date::date < '{year}-01-01' and sl2.usage = 'internal') then sml.qty_done
                                else 0 end ) as ton_dau_ky,		
                           sum(
                               case 
                               when(sm.date::date between '{year}-01-01' and '{year}-12-31' and sl2.usage = 'internal' and 
                                 sm.picking_id is not null and sp.picking_type_id not in (SELECT spt.id FROM stock_picking_type spt WHERE x_type = 'type_8')) then sml.qty_done
                               ELSE 0 end )as nhap_trong_ky,
                           sum(
                               case 
                               when(sm.picking_id is not null and sm.date::date between '{year}-01-01' and '{year}-12-31' and sl1.usage = 'internal') then sml.qty_done
                               ELSE 0 end )as xuat_trong_ky,
                           sum(
                               case 
                               when(sm.date::date between '{year}-01-01' and '{year}-12-31' and sl2.usage = 'internal' and 
                               sm.picking_id is not null and sp.picking_type_id in (SELECT spt.id FROM stock_picking_type spt WHERE x_type = 'type_8')) then sml.qty_done
                               ELSE 0 end )as nhap_tra_lai,
                           sum(
                               case
                               when(sml.date::date between '{year}-01-01' and '{year}-12-31' and sl1.usage = 'internal' and sm.inventory_id is not null) then -sml.qty_done
                               when(sml.date::date between '{year}-01-01' and '{year}-12-31' and sl2.usage = 'internal' and sm.inventory_id is not null) then sml.qty_done
                               else 0 end ) as kiem_ke_kho,
                           sum(
                               case
                               when(sml.date::date < '{year}-12-31' and sl1.usage = 'internal') then -sml.qty_done
                               when(sml.date::date < '{year}-12-31' and sl2.usage = 'internal') then sml.qty_done
                               else 0 end ) as ton_cuoi_ky,
                           pt.min_inventory as ton_kho_toi_thieu, pt.max_inventory as ton_kho_toi_da,
                           case when sum(pol.product_qty - pol.qty_received) > 0 then sum(pol.product_qty - pol.qty_received) else 0 end as SL_thuc_te,														
                           sum(
                               case 
                               when(extract(month from sm.date) = 1 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t1,																
                           sum(
                               case 
                               when(extract(month from sm.date) = 2 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null ) then sml.qty_done
                               ELSE 0 end )as slsd_t2,
                           sum(
                               case 
                               when(extract(month from sm.date) = 3 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t3,
                           sum(
                               case 
                               when(extract(month from sm.date) = 4 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null ) then sml.qty_done
                               ELSE 0 end )as slsd_t4,
                           sum(
                               case 
                               when(extract(month from sm.date) = 5 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t5,
                           sum(
                               case 
                               when(extract(month from sm.date) = 6 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t6,
                           sum(
                               case 
                               when(extract(month from sm.date) = 7 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t7,
                           sum(
                               case 
                               when(extract(month from sm.date) = 8 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t8,
                           sum(
                               case 
                               when(extract(month from sm.date) = 9 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t9,
                           sum(
                               case 
                               when(extract(month from sm.date) = 10 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t10,
                           sum(
                               case 
                               when(extract(month from sm.date) = 11 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t11,
                           sum(
                               case 
                               when(extract(month from sm.date) = 12 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t12,
                           sum(
                               case 
                               when(extract(month from sm.date) = 1 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t1,
                           sum(
                               case 
                               when(extract(month from sm.date) = 2 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t2,
                           sum(
                               case 
                               when(extract(month from sm.date) = 3 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t3,
                           sum(
                               case 
                               when(extract(month from sm.date) = 4 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t4,
                           sum(
                               case 
                               when(extract(month from sm.date) = 5 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t5,
                           sum(
                               case 
                               when(extract(month from sm.date) = 6 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t6,
                           sum(
                               case 
                               when(extract(month from sm.date) = 7 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t7,
                           sum(
                               case 
                               when(extract(month from sm.date) = 8 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t8,
                           sum(
                               case 
                               when(extract(month from sm.date) = 9 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t9,
                           sum(
                               case 
                               when(extract(month from sm.date) = 10 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t10,
                           sum(
                               case 
                               when(extract(month from sm.date) = 11 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t11,
                           sum(
                               case 
                               when(extract(month from sm.date) = 12 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t12,
                           sum(
                               case 
                               when(sm.date::date < '{year}-01-01' and sl1.usage = 'internal' and 
                               sm.picking_id is not null ) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end
                              ) as gtsd_cac_nam_truoc,                              
                           sum(
                               case 
                               when(sm.date::date <= '{year}-12-31' and sl2.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end) 
                               - sum (
                                       case 
                                       when(sm.date::date <= '{year}-12-31' and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                                       ELSE 0 end
                                       ) as gt_ton_kho
               FROM product_template pt
                       LEFT JOIN uom_uom uu  ON uu.id = pt.uom_id
                       LEFT JOIN product_product pp  ON pt.id = pp.product_tmpl_id
                       LEFT JOIN stock_move sm ON sm.product_id = pp.id
                       left join stock_valuation_layer svl on svl.stock_move_id = sm.id 
                       LEFT JOIN stock_move_line sml ON sml.move_id = sm.id 
                       LEFT JOIN stock_picking sp  ON sm.picking_id = sp.id
                       LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                       left join stock_inventory si on sm.inventory_id=si.id
                       left join stock_location sl1 on sm.location_id=sl1.id
                       left join stock_location sl2 on sm.location_dest_id=sl2.id
                       left join ir_translation it on it."name" = 'stock.picking.type,name' and it.lang = 'vi_VN' and it.src = spt."name"
                       left join ir_translation it2 on it2."name" = 'uom.uom,name' and it2.lang = 'vi_VN' and it2.src = uu."name"
                       LEFT JOIN purchase_order_line pol on sm.purchase_line_id = pol.id
                       left join purchase_order po on po.id = pol.order_id 
                       left join ir_property ip on ip.name = 'standard_price' and substring(ip.res_id,17,100)::int = pp.id
               where sm.state = 'done' and pt.x_type = 'product' and pt.active = 't'
               and pt.x_product_type = 'supplies' 
               and sl1.id != sl2.id 
               and (sl1.usage = 'internal' or sl2.usage = 'internal') 
               and (sl1.id in {stock} or sl2.id in {stock})
               and (sp.state = 'done' or si.state = 'done')
               and not (sl1.usage = 'internal' and sl2.usage = 'internal')
               GROUP BY pp.id,pt.default_code,pt.name,pt.x_supplies_type, pt.x_product_company,pt.x_code_brand, uu.name,ip.value_float, pt.min_inventory, pt.max_inventory,it2.value)
            SELECT * from dt
            WHERE  (dt.ton_dau_ky+dt.nhap_trong_ky-dt.xuat_trong_ky+dt.nhap_tra_lai+dt.kiem_ke_kho) < dt.ton_kho_toi_thieu
           '''.format(year=current_year, stock=tuple(stock + [0, 0]))
        else:
            sql = '''
                   SELECT pp.id as ma_sp ,pt.default_code as ma_hang, pt.name as ten_sp, 
                       case when pt.x_supplies_type = 'supplies' then 'Vật tư tiêu chuẩn'
                        when pt.x_supplies_type = 'labor_protection' then 'Bảo hộ lao động'
                        when pt.x_supplies_type = 'stationery' then 'Văn phòng phẩm'
                        when pt.x_supplies_type = 'supplies_project' then 'Vật tư xuất cho dự án' end as phan_loai,
                       pt.x_product_company as hang_sx,
                       pt.x_code_brand as  model,
                       coalesce(it2.value,uu."name") as don_vi,
                       ip.value_float as don_gia,		 
                            sum(
                                case
                                when(sml.date::date < '{year}-01-01' and sl1.usage = 'internal') then -sml.qty_done
                                when(sml.date::date < '{year}-01-01' and sl2.usage = 'internal') then sml.qty_done
                                else 0 end ) as ton_dau_ky,		
                           sum(
                               case 
                               when(sm.date::date between '{year}-01-01' and '{year}-12-31' and sl2.usage = 'internal' and 
                                 sm.picking_id is not null and sp.picking_type_id not in (SELECT spt.id FROM stock_picking_type spt WHERE x_type = 'type_8')) then sml.qty_done
                               ELSE 0 end )as nhap_trong_ky,
                           sum(
                               case 
                               when(sm.picking_id is not null and sm.date::date between '{year}-01-01' and '{year}-12-31' and sl1.usage = 'internal') then sml.qty_done
                               ELSE 0 end )as xuat_trong_ky,
                           sum(
                               case 
                               when(sm.date::date between '{year}-01-01' and '{year}-12-31' and sl2.usage = 'internal' and 
                               sm.picking_id is not null and sp.picking_type_id in (SELECT spt.id FROM stock_picking_type spt WHERE x_type = 'type_8')) then sml.qty_done
                               ELSE 0 end )as nhap_tra_lai,
                           sum(
                               case
                               when(sml.date::date between '{year}-01-01' and '{year}-12-31' and sl1.usage = 'internal' and sm.inventory_id is not null) then -sml.qty_done
                               when(sml.date::date between '{year}-01-01' and '{year}-12-31' and sl2.usage = 'internal' and sm.inventory_id is not null) then sml.qty_done
                               else 0 end ) as kiem_ke_kho,
                           sum(
                               case
                               when(sml.date::date < '{year}-12-31' and sl1.usage = 'internal') then -sml.qty_done
                               when(sml.date::date < '{year}-12-31' and sl2.usage = 'internal') then sml.qty_done
                               else 0 end ) as ton_cuoi_ky,
                           pt.min_inventory as ton_kho_toi_thieu, pt.max_inventory as ton_kho_toi_da,
                           case when sum(pol.product_qty - pol.qty_received) > 0 then sum(pol.product_qty - pol.qty_received) else 0 end as SL_thuc_te,														
                           sum(
                               case 
                               when(extract(month from sm.date) = 1 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t1,																
                           sum(
                               case 
                               when(extract(month from sm.date) = 2 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null ) then sml.qty_done
                               ELSE 0 end )as slsd_t2,
                           sum(
                               case 
                               when(extract(month from sm.date) = 3 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t3,
                           sum(
                               case 
                               when(extract(month from sm.date) = 4 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null ) then sml.qty_done
                               ELSE 0 end )as slsd_t4,
                           sum(
                               case 
                               when(extract(month from sm.date) = 5 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t5,
                           sum(
                               case 
                               when(extract(month from sm.date) = 6 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t6,
                           sum(
                               case 
                               when(extract(month from sm.date) = 7 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t7,
                           sum(
                               case 
                               when(extract(month from sm.date) = 8 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t8,
                           sum(
                               case 
                               when(extract(month from sm.date) = 9 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t9,
                           sum(
                               case 
                               when(extract(month from sm.date) = 10 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t10,
                           sum(
                               case 
                               when(extract(month from sm.date) = 11 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t11,
                           sum(
                               case 
                               when(extract(month from sm.date) = 12 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done
                               ELSE 0 end )as slsd_t12,
                           sum(
                               case 
                               when(extract(month from sm.date) = 1 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t1,
                           sum(
                               case 
                               when(extract(month from sm.date) = 2 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t2,
                           sum(
                               case 
                               when(extract(month from sm.date) = 3 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t3,
                           sum(
                               case 
                               when(extract(month from sm.date) = 4 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t4,
                           sum(
                               case 
                               when(extract(month from sm.date) = 5 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t5,
                           sum(
                               case 
                               when(extract(month from sm.date) = 6 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t6,
                           sum(
                               case 
                               when(extract(month from sm.date) = 7 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t7,
                           sum(
                               case 
                               when(extract(month from sm.date) = 8 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t8,
                           sum(
                               case 
                               when(extract(month from sm.date) = 9 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t9,
                           sum(
                               case 
                               when(extract(month from sm.date) = 10 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t10,
                           sum(
                               case 
                               when(extract(month from sm.date) = 11 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t11,
                           sum(
                               case 
                               when(extract(month from sm.date) = 12 and extract(year from sm.date) = {year} and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end )as gtsd_t12,
                           sum(
                               case 
                               when(sm.date::date < '{year}-01-01' and sl1.usage = 'internal' and 
                               sm.picking_id is not null ) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end
                              ) as gtsd_cac_nam_truoc,                              
                           sum(
                               case 
                               when(sm.date::date <= '{year}-12-31' and sl2.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                               ELSE 0 end) 
                               - sum (
                                       case 
                                       when(sm.date::date <= '{year}-12-31' and sl1.usage = 'internal' and 
                               sm.picking_id is not null) then sml.qty_done*coalesce(svl.unit_cost,0)
                                       ELSE 0 end
                                       ) as gt_ton_kho
               FROM product_template pt
                       LEFT JOIN uom_uom uu  ON uu.id = pt.uom_id
                       LEFT JOIN product_product pp  ON pt.id = pp.product_tmpl_id
                       LEFT JOIN stock_move sm ON sm.product_id = pp.id
                       left join stock_valuation_layer svl on svl.stock_move_id = sm.id 
                       LEFT JOIN stock_move_line sml ON sml.move_id = sm.id 
                       LEFT JOIN stock_picking sp  ON sm.picking_id = sp.id
                       LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                       left join stock_inventory si on sm.inventory_id=si.id
                       left join stock_location sl1 on sm.location_id=sl1.id
                       left join stock_location sl2 on sm.location_dest_id=sl2.id
                       left join ir_translation it on it."name" = 'stock.picking.type,name' and it.lang = 'vi_VN' and it.src = spt."name"
                       left join ir_translation it2 on it2."name" = 'uom.uom,name' and it2.lang = 'vi_VN' and it2.src = uu."name"
                       LEFT JOIN purchase_order_line pol on sm.purchase_line_id = pol.id
                       left join purchase_order po on po.id = pol.order_id 
                       left join ir_property ip on ip.name = 'standard_price' and substring(ip.res_id,17,100)::int = pp.id
               where sm.state = 'done' and pt.x_type = 'product' and pt.active = 't'
               and pt.x_product_type = 'supplies' 
               and sl1.id != sl2.id 
               and (sl1.usage = 'internal' or sl2.usage = 'internal') 
               and (sl1.id in {stock} or sl2.id in {stock})
               and (sp.state = 'done' or si.state = 'done')
               and not (sl1.usage = 'internal' and sl2.usage = 'internal')
               GROUP BY pp.id,pt.default_code,pt.name,pt.x_supplies_type, pt.x_product_company,pt.x_code_brand, uu.name,ip.value_float, pt.min_inventory, pt.max_inventory,it2.value
            '''.format(year=current_year, stock=tuple(stock + [0, 0]))
        # print(sql)
        self._cr.execute(sql)
        recs = self._cr.dictfetchall()

        highlight = NamedStyle(name="highlight")
        bd1 = Side(style='thin', color="000000")
        bd2 = Side(style='dotted', color="000000")
        bd3 = Side(style='none')
        highlight.border = Border(left=bd1, top=bd2, right=bd1, bottom=bd2)

        style_sum1 = NamedStyle(name="style_sum1")
        style_sum1.PatternFill = Font(color='0099CC00')
        style_sum1.number_format = '#,##0'
        style_sum1.border = Border(left=bd1, top=bd1, right=bd1, bottom=bd2)

        highlight1 = NamedStyle(name="highlight1")
        highlight1.font = Font(name='Verdana', size=12,bold=True)
        highlight1.border = Border(left=bd1, top=bd1, right=bd1, bottom=bd1)
        highlight1.alignment = Alignment(horizontal='center', vertical='center', wrapText=True)

        row = 7
        x = 1

        for r in recs:
            ws.cell(row, 1).value = x
            ws.cell(row, 2).value, ws.cell(row, 2).style = r['ma_hang'],highlight1
            ws.cell(row, 3).value = r['ten_sp']
            ws.cell(row, 4).value = r['phan_loai']
            ws.cell(row, 5).value = r['hang_sx']
            ws.cell(row, 6).value = r['model']
            ws.cell(row, 7).value = r['don_vi']
            ws.cell(row, 8).value = r['don_gia']
            ws.cell(row, 9).value = r['ton_dau_ky']
            ws.cell(row, 10).value = r['nhap_trong_ky']
            ws.cell(row, 11).value = r['xuat_trong_ky']
            ws.cell(row, 12).value = r['nhap_tra_lai']
            ws.cell(row, 13).value = r['kiem_ke_kho']
            ws.cell(row, 14).value = '=(I%s+J%s-K%s+L%s+M%s)' % (row, row, row, row, row)
            ws.cell(row, 15).value = r['ton_kho_toi_thieu']
            ws.cell(row, 16).value = r['ton_kho_toi_da']
            ws.cell(row, 17).value = '=IF(N%s>=O%s,0,P%s-O%s)' % (row, row, row, row)
            ws.cell(row, 18).value = r['sl_thuc_te']
            ws.cell(row, 19).value, ws.cell(row, 19).style = r['slsd_t1'], style_sum1
            ws.cell(row, 20).value, ws.cell(row, 20).style = r['slsd_t2'], style_sum1
            ws.cell(row, 21).value, ws.cell(row, 21).style = r['slsd_t3'], style_sum1
            ws.cell(row, 22).value, ws.cell(row, 22).style = r['slsd_t4'], style_sum1
            ws.cell(row, 23).value, ws.cell(row, 23).style = r['slsd_t5'], style_sum1
            ws.cell(row, 24).value, ws.cell(row, 24).style = r['slsd_t6'], style_sum1
            ws.cell(row, 25).value, ws.cell(row, 25).style = r['slsd_t7'], style_sum1
            ws.cell(row, 26).value, ws.cell(row, 26).style = r['slsd_t8'], style_sum1
            ws.cell(row, 27).value, ws.cell(row, 27).style = r['slsd_t9'], style_sum1
            ws.cell(row, 28).value, ws.cell(row, 28).style = r['slsd_t10'], style_sum1
            ws.cell(row, 29).value, ws.cell(row, 29).style = r['slsd_t11'], style_sum1
            ws.cell(row, 30).value, ws.cell(row, 30).style = r['slsd_t12'], style_sum1
            ws.cell(row, 31).value, ws.cell(row, 31).style = r['gtsd_t1'], style_sum1
            ws.cell(row, 32).value, ws.cell(row, 32).style = r['gtsd_t2'], style_sum1
            ws.cell(row, 33).value, ws.cell(row, 33).style = r['gtsd_t3'], style_sum1
            ws.cell(row, 34).value, ws.cell(row, 34).style = r['gtsd_t4'], style_sum1
            ws.cell(row, 35).value, ws.cell(row, 35).style = r['gtsd_t5'], style_sum1
            ws.cell(row, 36).value, ws.cell(row, 36).style = r['gtsd_t6'], style_sum1
            ws.cell(row, 37).value, ws.cell(row, 37).style = r['gtsd_t7'], style_sum1
            ws.cell(row, 38).value, ws.cell(row, 38).style = r['gtsd_t8'], style_sum1
            ws.cell(row, 39).value, ws.cell(row, 39).style = r['gtsd_t9'], style_sum1
            ws.cell(row, 40).value, ws.cell(row, 40).style = r['gtsd_t10'], style_sum1
            ws.cell(row, 41).value, ws.cell(row, 41).style = r['gtsd_t11'], style_sum1
            ws.cell(row, 42).value, ws.cell(row, 42).style = r['gtsd_t12'], style_sum1
            ws.cell(row, 43).value, ws.cell(row, 43).style = r['gtsd_cac_nam_truoc'], style_sum1
            ws.cell(row, 44).value, ws.cell(row, 44).style = '=SUM(AE%s:AP%s)' % (row, row),style_sum1
            ws.cell(row, 45).value, ws.cell(row, 45).style = r['gt_ton_kho'], style_sum1
            ws.cell(row, 46).value, ws.cell(row, 46).style = '=(AQ%s+AR%s)' % (row, row),style_sum1

            x += 1
            row += 1

        stream = BytesIO(save_virtual_workbook(wb))
        xls = stream.getvalue()

        attachment_id = self.env['ir.attachment'].create({
            'name': 'Báo cáo tồn kho vật tư.xlsx',
            'datas': base64.b64encode(xls),
            'type': 'binary',
        })
        # download
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(attachment_id.id) + '?download=true',
            'target': 'new',
        }
