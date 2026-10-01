import { api, type Paginated } from '../services/api'
import type { Member, MemberPayload, MemberStatus, MemberWithStats } from '../types/member'
import type { Sale } from '../types/sale'

export function getMembers(params: { search?: string; status?: MemberStatus | '' } = {}): Promise<Member[]> {
  return api.get<Member[]>('/api/members', { search: params.search, status: params.status || undefined })
}

export function getMember(id: string): Promise<MemberWithStats> {
  return api.get<MemberWithStats>(`/api/members/${id}`)
}

export function getMemberTransactions(id: string, page = 1, pageSize = 10): Promise<Paginated<Sale>> {
  return api.paginated<Sale>(`/api/members/${id}/transactions`, { page, pageSize })
}

export function createMember(data: MemberPayload): Promise<Member> {
  return api.post<Member>('/api/members', data)
}

export function updateMember(id: string, data: MemberPayload): Promise<Member> {
  return api.put<Member>(`/api/members/${id}`, data)
}

export function deactivateMember(id: string): Promise<Member> {
  return api.delete<Member>(`/api/members/${id}`)
}

// Self-service anggota
export function getMyMemberProfile(): Promise<MemberWithStats> {
  return api.get<MemberWithStats>('/api/members/me')
}

export function getMyTransactions(page = 1, pageSize = 10): Promise<Paginated<Sale>> {
  return api.paginated<Sale>('/api/members/me/transactions', { page, pageSize })
}

export function getMyTransaction(id: string): Promise<Sale> {
  return api.get<Sale>(`/api/members/me/transactions/${id}`)
}
