export type ExpenseCategory =
  | 'ELECTRICITY'
  | 'WATER'
  | 'INTERNET'
  | 'TRANSPORTATION'
  | 'OFFICE_SUPPLIES'
  | 'MAINTENANCE'
  | 'OTHER'

export const EXPENSE_CATEGORY_LABELS: Record<ExpenseCategory, string> = {
  ELECTRICITY: 'Listrik',
  WATER: 'Air',
  INTERNET: 'Internet',
  TRANSPORTATION: 'Transportasi',
  OFFICE_SUPPLIES: 'ATK',
  MAINTENANCE: 'Perawatan',
  OTHER: 'Operasional lainnya',
}

export interface Expense {
  id: string
  expenseNumber: string
  category: ExpenseCategory
  description: string
  amount: number
  date: string
  createdBy: string
  createdByName: string | null
  createdAt: string
  updatedAt: string
}

export interface ExpensePayload {
  category: ExpenseCategory
  description: string
  amount: number
  date: string
}
