import { api } from '../services/api'
import type { Category, CategoryPayload } from '../types/category'

export function getCategories(params: { search?: string; isActive?: boolean } = {}): Promise<Category[]> {
  return api.get<Category[]>('/api/categories', { search: params.search, isActive: params.isActive })
}

export function createCategory(data: CategoryPayload): Promise<Category> {
  return api.post<Category>('/api/categories', data)
}

export function updateCategory(id: string, data: CategoryPayload): Promise<Category> {
  return api.put<Category>(`/api/categories/${id}`, data)
}

export function deactivateCategory(id: string): Promise<Category> {
  return api.delete<Category>(`/api/categories/${id}`)
}
