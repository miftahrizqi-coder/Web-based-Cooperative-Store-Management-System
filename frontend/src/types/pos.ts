// Tipe POS memakai tipe domain bersama.
import type { Member } from './member'
import type { Product } from './product'

export type { PaymentMethod, CreateSalePayload, Sale as SaleResponse } from './sale'
export type { MemberStatus } from './member'

export type POSProduct = Product
export type POSMember = Member

export interface CartItem {
  product: POSProduct
  quantity: number
}
