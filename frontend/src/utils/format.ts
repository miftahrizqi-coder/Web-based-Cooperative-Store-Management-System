const currencyFormatter = new Intl.NumberFormat('id-ID', {
  style: 'currency',
  currency: 'IDR',
  maximumFractionDigits: 0,
})

const numberFormatter = new Intl.NumberFormat('id-ID', { maximumFractionDigits: 2 })

export function formatCurrency(value: number | null | undefined): string {
  return currencyFormatter.format(Number(value) || 0)
}

export function formatNumber(value: number | null | undefined): string {
  return numberFormatter.format(Number(value) || 0)
}

export function formatSigned(value: number): string {
  return `${value > 0 ? '+' : ''}${formatNumber(value)}`
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium' }).format(date)
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

/** YYYY-MM-DD untuk <input type="date"> dalam zona waktu lokal. */
export function toDateInput(value: Date | string = new Date()): string {
  const date = typeof value === 'string' ? new Date(value) : value
  const offset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - offset).toISOString().slice(0, 10)
}

export function firstDayOfMonth(): string {
  const now = new Date()
  return toDateInput(new Date(now.getFullYear(), now.getMonth(), 1))
}

/** Tanggal input (YYYY-MM-DD) -> ISO datetime tengah hari lokal. */
export function dateInputToIso(value: string): string {
  return new Date(`${value}T12:00:00`).toISOString()
}

/** Ekspor tabel ke CSV (dibuka di Excel). PRD Phase 7: Export Excel. */
export function downloadCsv(filename: string, headers: string[], rows: (string | number | null | undefined)[][]) {
  const escape = (value: string | number | null | undefined) => {
    const text = value === null || value === undefined ? '' : String(value)
    return /[",;\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
  }
  const csv = [headers, ...rows].map((row) => row.map(escape).join(';')).join('\n')
  const blob = new Blob([`﻿${csv}`], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename.endsWith('.csv') ? filename : `${filename}.csv`
  link.click()
  URL.revokeObjectURL(url)
}
