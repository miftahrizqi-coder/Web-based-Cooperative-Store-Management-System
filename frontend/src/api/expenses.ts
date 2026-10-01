import { api, type Paginated } from '../services/api'
import type { Expense, ExpenseCategory, ExpensePayload } from '../types/expense'

export function getExpenses(params: {
  category?: ExpenseCategory | ''
  search?: string
  dateFrom?: string
  dateTo?: string
  page?: number
  pageSize?: number
} = {}): Promise<Paginated<Expense>> {
  return api.paginated<Expense>('/api/expenses', {
    ...params,
    category: params.category || undefined,
    page: params.page ?? 1,
    pageSize: params.pageSize ?? 20,
  })
}

export function createExpense(data: ExpensePayload): Promise<Expense> {
  return api.post<Expense>('/api/expenses', data)
}

export function updateExpense(id: string, data: ExpensePayload): Promise<Expense> {
  return api.put<Expense>(`/api/expenses/${id}`, data)
}

export function deleteExpense(id: string): Promise<void> {
  return api.delete<void>(`/api/expenses/${id}`)
}
