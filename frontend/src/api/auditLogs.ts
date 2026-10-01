import { api, type Paginated } from '../services/api'
import type { AuditLog } from '../types/audit'

export function getAuditLogs(params: {
  module?: string
  action?: string
  search?: string
  dateFrom?: string
  dateTo?: string
  page?: number
  pageSize?: number
} = {}): Promise<Paginated<AuditLog>> {
  return api.paginated<AuditLog>('/api/audit-logs', {
    ...params,
    module: params.module || undefined,
    action: params.action || undefined,
    page: params.page ?? 1,
    pageSize: params.pageSize ?? 50,
  })
}
