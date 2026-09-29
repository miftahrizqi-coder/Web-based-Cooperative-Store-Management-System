import type {
  Activity,
  ActivityEntityType,
  ActivityType,
  GoodsReceipt,
  GoodsReceiptPayload,
  Purchase,
  PurchaseOrder,
  PurchaseOrderPayload,
  PurchasePayload,
  SupplierInvoice,
  SupplierInvoicePayload,
  SupplierPayable,
  SupplierPayment,
  SupplierPaymentPayload,
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

export async function getGoodsReceipts(
  accessToken: string,
): Promise<GoodsReceipt[]> {
  const response = await fetch('/api/goods-receipts', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal mengambil daftar penerimaan barang.',
      ),
    )
  }

  return response.json()
}

export async function getGoodsReceipt(
  accessToken: string,
  receiptId: string,
): Promise<GoodsReceipt> {
  const response = await fetch(
    `/api/goods-receipts/${receiptId}`,
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
        'Gagal mengambil detail penerimaan barang.',
      ),
    )
  }

  return response.json()
}

export async function createGoodsReceipt(
  accessToken: string,
  data: GoodsReceiptPayload,
): Promise<GoodsReceipt> {
  const response = await fetch('/api/goods-receipts', {
    method: 'POST',
    headers: authHeaders(accessToken),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal membuat penerimaan barang.',
      ),
    )
  }

  return response.json()
}

export async function getPurchases(
  accessToken: string,
): Promise<Purchase[]> {
  const response = await fetch('/api/purchases', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal mengambil daftar purchase.',
      ),
    )
  }

  return response.json()
}

export async function getPurchase(
  accessToken: string,
  purchaseId: string,
): Promise<Purchase> {
  const response = await fetch(
    `/api/purchases/${purchaseId}`,
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
        'Gagal mengambil detail purchase.',
      ),
    )
  }

  return response.json()
}

export async function createPurchase(
  accessToken: string,
  data: PurchasePayload,
): Promise<Purchase> {
  const response = await fetch('/api/purchases', {
    method: 'POST',
    headers: authHeaders(accessToken),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal membuat purchase.',
      ),
    )
  }

  return response.json()
}

export async function getSupplierInvoices(
  accessToken: string,
): Promise<SupplierInvoice[]> {
  const response = await fetch('/api/supplier-invoices', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal mengambil daftar supplier invoice.',
      ),
    )
  }

  return response.json()
}

export async function getSupplierInvoice(
  accessToken: string,
  invoiceId: string,
): Promise<SupplierInvoice> {
  const response = await fetch(
    `/api/supplier-invoices/${invoiceId}`,
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
        'Gagal mengambil detail supplier invoice.',
      ),
    )
  }

  return response.json()
}

export async function createSupplierInvoice(
  accessToken: string,
  data: SupplierInvoicePayload,
): Promise<SupplierInvoice> {
  const response = await fetch('/api/supplier-invoices', {
    method: 'POST',
    headers: authHeaders(accessToken),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal membuat supplier invoice.',
      ),
    )
  }

  return response.json()
}

export async function getSupplierPayables(
  accessToken: string,
): Promise<SupplierPayable[]> {
  const response = await fetch('/api/supplier-payables', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal mengambil daftar hutang supplier.',
      ),
    )
  }

  return response.json()
}

export async function getSupplierPayments(
  accessToken: string,
): Promise<SupplierPayment[]> {
  const response = await fetch('/api/supplier-payments', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal mengambil daftar pembayaran supplier.',
      ),
    )
  }

  return response.json()
}

export async function createSupplierPayment(
  accessToken: string,
  data: SupplierPaymentPayload,
): Promise<SupplierPayment> {
  const response = await fetch('/api/supplier-payments', {
    method: 'POST',
    headers: authHeaders(accessToken),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Gagal mencatat pembayaran supplier.',
      ),
    )
  }

  return response.json()
}

export async function getActivities(
  accessToken: string,
  params?: {
    entityType?: ActivityEntityType
    activityType?: ActivityType
  },
): Promise<Activity[]> {
  const searchParams = new URLSearchParams()

  if (params?.entityType) {
    searchParams.set(
      'entityType',
      params.entityType,
    )
  }

  if (params?.activityType) {
    searchParams.set(
      'activityType',
      params.activityType,
    )
  }

  const query = searchParams.toString()

  const response = await fetch(
    `/api/activities${query ? `?${query}` : ''}`,
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
        'Gagal mengambil Activity Timeline.',
      ),
    )
  }

  return response.json()
}