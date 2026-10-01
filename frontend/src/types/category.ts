export interface Category {
  id: string
  name: string
  description: string | null
  isActive: boolean
  productCount: number
  createdAt: string
  updatedAt: string
}

export interface CategoryPayload {
  name: string
  description: string | null
  isActive: boolean
}
