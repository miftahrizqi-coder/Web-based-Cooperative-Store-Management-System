import type {
  PurchaseOrder,
  PurchaseOrderPayload,
} from '../types/procurement'

function authHeaders(accessToken: string) {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${accessToken}`,
  }
}

async function getErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const body = await response.json()

    if (typeof body?.detail === 'string') {
      return body.detail
    }
  } catch {
    // Ignore malformed error responses.
  }

  return fallback
}

export async function getPurchaseOrders(
  accessToken: string,
): Promise<PurchaseOrder[]> {
  const response = await fetch('/api/purchase-orders', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal mengambil daftar purchase order.',
      ),
    )
  }

  return response.json()
}

export async function getPurchaseOrder(
  accessToken: string,
  purchaseOrderId: string,
): Promise<PurchaseOrder> {
  const response = await fetch(
    `/api/purchase-orders/${purchaseOrderId}`,
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
        'Gagal mengambil detail purchase order.',
      ),
    )
  }

  return response.json()
}

export async function createPurchaseOrder(
  accessToken: string,
  data: PurchaseOrderPayload,
): Promise<PurchaseOrder> {
  const response = await fetch('/api/purchase-orders', {
    method: 'POST',
    headers: authHeaders(accessToken),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal membuat purchase order.',
      ),
    )
  }

  return response.json()
}

export async function updatePurchaseOrder(
  accessToken: string,
  purchaseOrderId: string,
  data: PurchaseOrderPayload,
): Promise<PurchaseOrder> {
  const response = await fetch(
    `/api/purchase-orders/${purchaseOrderId}`,
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
        'Gagal memperbarui purchase order.',
      ),
    )
  }

  return response.json()
}

async function runPurchaseOrderAction(
  accessToken: string,
  purchaseOrderId: string,
  action: 'submit' | 'approve' | 'order' | 'cancel',
): Promise<PurchaseOrder> {
  const response = await fetch(
    `/api/purchase-orders/${purchaseOrderId}/${action}`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        `Gagal menjalankan aksi ${action} pada purchase order.`,
      ),
    )
  }

  return response.json()
}

export async function submitPurchaseOrder(
  accessToken: string,
  purchaseOrderId: string,
): Promise<PurchaseOrder> {
  return runPurchaseOrderAction(
    accessToken,
    purchaseOrderId,
    'submit',
  )
}

export async function approvePurchaseOrder(
  accessToken: string,
  purchaseOrderId: string,
): Promise<PurchaseOrder> {
  return runPurchaseOrderAction(
    accessToken,
    purchaseOrderId,
    'approve',
  )
}

export async function orderPurchaseOrder(
  accessToken: string,
  purchaseOrderId: string,
): Promise<PurchaseOrder> {
  return runPurchaseOrderAction(
    accessToken,
    purchaseOrderId,
    'order',
  )
}

export async function cancelPurchaseOrder(
  accessToken: string,
  purchaseOrderId: string,
): Promise<PurchaseOrder> {
  return runPurchaseOrderAction(
    accessToken,
    purchaseOrderId,
    'cancel',
  )
}