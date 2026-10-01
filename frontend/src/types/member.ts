export type MemberStatus = 'ACTIVE' | 'INACTIVE'

export interface Member {
  id: string
  memberNumber: string
  name: string
  phone: string
  email: string | null
  address: string | null
  joinedAt: string
  status: MemberStatus
  createdAt: string
  updatedAt: string
}

export interface MemberWithStats extends Member {
  transactionCount: number
  totalSpending: number
  lastTransactionAt: string | null
  hasUserAccount: boolean
}

export interface MemberPayload {
  memberNumber: string | null
  name: string
  phone: string
  email: string | null
  address: string | null
  joinedAt: string | null
  status: MemberStatus
}
