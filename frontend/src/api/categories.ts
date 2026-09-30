export interface Category {
  id: string
  name: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CategoryPayload {
  name: string
  description: string | null
}

export interface CategoryStatusPayload {
  is_active: boolean
}

async function getErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const data = await response.json()

    if (typeof data?.detail === 'string') {
      return data.detail
    }

    if (Array.isArray(data?.detail)) {
      const message = data.detail
        .map((item: { msg?: string }) => item.msg)
        .filter(Boolean)
        .join(', ')

      if (message) return message
    }
  } catch {
    // Ignore invalid response body.
  }

  return fallback
}

function authHeaders(accessToken: string) {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${accessToken}`,
  }
}

export async function getCategories(
  accessToken: string,
  isActive?: boolean,
): Promise<Category[]> {
  const query = new URLSearchParams()

  if (isActive !== undefined) {
    query.set('is_active', String(isActive))
  }

  const queryString = query.toString()

  const response = await fetch(
    `/api/categories${queryString ? `?${queryString}` : ''}`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal mengambil data Category.',
      ),
    )
  }

  return response.json() as Promise<Category[]>
}

export async function getCategory(
  accessToken: string,
  categoryId: string,
): Promise<Category> {
  const response = await fetch(`/api/categories/${categoryId}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal mengambil detail Category.',
      ),
    )
  }

  return response.json() as Promise<Category>
}

export async function createCategory(
  accessToken: string,
  data: CategoryPayload,
): Promise<Category> {
  const response = await fetch('/api/categories', {
    method: 'POST',
    headers: authHeaders(accessToken),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal membuat Category.',
      ),
    )
  }

  return response.json() as Promise<Category>
}

export async function updateCategory(
  accessToken: string,
  categoryId: string,
  data: CategoryPayload,
): Promise<Category> {
  const response = await fetch(
    `/api/categories/${categoryId}`,
    {
      method: 'PUT',
      headers: authHeaders(accessToken),
      body: JSON.stringify(data),
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal memperbarui Category.',
      ),
    )
  }

  return response.json() as Promise<Category>
}

export async function updateCategoryStatus(
  accessToken: string,
  categoryId: string,
  isActive: boolean,
): Promise<Category> {
  const response = await fetch(
    `/api/categories/${categoryId}/status`,
    {
      method: 'PATCH',
      headers: authHeaders(accessToken),
      body: JSON.stringify({
        is_active: isActive,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal memperbarui status Category.',
      ),
    )
  }

  return response.json() as Promise<Category>
}

export async function deleteCategory(
  accessToken: string,
  categoryId: string,
): Promise<void> {
  const response = await fetch(
    `/api/categories/${categoryId}`,
    {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal menghapus Category.',
      ),
    )
  }
}