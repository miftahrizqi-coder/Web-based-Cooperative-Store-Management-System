export type SupplierStatus =
  | 'ACTIVE'
  | 'INACTIVE'
  | 'BLACKLISTED'

export type SupplierPaymentTermType =
  | 'CASH'
  | 'CREDIT'

export interface SupplierAddress {
  street: string
  city: string
  province: string
  postalCode: string
}

export interface SupplierPaymentTerm {
  type: SupplierPaymentTermType
  days: number
}

export interface SupplierBankAccount {
  bankName: string
  accountNumber: string
  accountName: string
}

export interface Supplier {
  id: string
  supplierCode: string
  name: string
  companyName: string
  contactPerson: string
  phone: string
  email: string
  address: SupplierAddress
  paymentTerm: SupplierPaymentTerm
  bankAccount: SupplierBankAccount | null
  status: SupplierStatus
  notes: string | null
  createdAt: string
  updatedAt: string
}

export interface CreateSupplierRequest {
  supplierCode: string
  name: string
  companyName: string
  contactPerson: string
  phone: string
  email: string
  address: SupplierAddress
  paymentTerm: SupplierPaymentTerm
  bankAccount: SupplierBankAccount | null
  status: SupplierStatus
  notes: string
}

export interface UpdateSupplierRequest {
  name: string
  companyName: string
  contactPerson: string
  phone: string
  email: string
  address: SupplierAddress
  paymentTerm: SupplierPaymentTerm
  bankAccount: SupplierBankAccount | null
  notes: string
}