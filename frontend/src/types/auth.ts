export type UserRole = 'admin' | 'kasir' | 'pengurus' | 'anggota'

export interface CurrentUser {
  id: string
  username: string
  email: string
  name: string
  role: UserRole
  is_active: boolean
  memberId: string | null
}

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: 'Admin',
  kasir: 'Kasir',
  pengurus: 'Pengurus',
  anggota: 'Anggota',
}
