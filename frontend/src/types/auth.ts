export type UserRole = 'admin' | 'kasir' | 'pengurus' | 'anggota'

export interface CurrentUser {
  id: string
  username: string
  email: string
  name: string
  role: UserRole
  is_active: boolean
}