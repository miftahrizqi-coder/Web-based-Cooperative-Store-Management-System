import type {
  CreateSupplierRequest,
  Supplier,
  SupplierStatus,
  UpdateSupplierRequest,
} from '../types/supplier'

async function parseError(
  response: Response,
  fallback: string,
): Promise<never> {
  try {
    const body = await response.json()

    if (typeof body.detail === 'string') {
      throw new Error(body.detail)
    }
  } catch (error) {
    if (error instanceof Error) {
      throw error
    }
  }

  throw new Error(fallback)
}

export async function getSuppliers(
  accessToken: string,
): Promise<Supplier[]> {
  const response = await fetch('/api/suppliers', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    return parseError(
      response,
      'Gagal mengambil data supplier.',
    )
  }

  return response.json()
}


export async function getSupplier(
  accessToken: string,
  supplierId: string,
): Promise<Supplier> {
  const response = await fetch(
    `/api/suppliers/${supplierId}`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  )

  if (!response.ok) {
    return parseError(
      response,
      'Gagal mengambil detail supplier.',
    )
  }

  return response.json()
}


export async function createSupplier(
  accessToken: string,
  data: CreateSupplierRequest,
): Promise<Supplier> {
  const response = await fetch('/api/suppliers', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    return parseError(
      response,
      'Gagal membuat supplier.',
    )
  }

  return response.json()
}


export async function updateSupplier(
  accessToken: string,
  supplierId: string,
  data: UpdateSupplierRequest,
): Promise<Supplier> {
  const response = await fetch(
    `/api/suppliers/${supplierId}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(data),
    },
  )

  if (!response.ok) {
    return parseError(
      response,
      'Gagal memperbarui supplier.',
    )
  }

  return response.json()
}


export async function updateSupplierStatus(
  accessToken: string,
  supplierId: string,
  status: SupplierStatus,
): Promise<Supplier> {
  const response = await fetch(
    `/api/suppliers/${supplierId}/status`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        status,
      }),
    },
  )

  if (!response.ok) {
    return parseError(
      response,
      'Gagal memperbarui status supplier.',
    )
  }

  return response.json()
}