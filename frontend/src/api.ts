const API_BASE_URL = "http://localhost:8000/api";

export async function getOrganizations() {
  const response = await fetch(`${API_BASE_URL}/organizations/`);

  if (!response.ok) {
    throw new Error("Failed to fetch organizations");
  }

  return response.json();
}

export async function getTransactions(organization: string) {
  const response = await fetch(`${API_BASE_URL}/transactions/`, {
    headers: {
      "X-Organization": organization,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch transactions");
  }

  return response.json();
}

export async function getLineItems(organization: string) {
  const response = await fetch(`${API_BASE_URL}/line-items/`, {
    headers: {
      "X-Organization": organization,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch line items");
  }

  return response.json();
}

export async function importBankStatement(
  organization: string,
  file: File
) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/import/`, {
    method: "POST",
    headers: {
      "X-Organization": organization,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to import bank statement");
  }

  return response.json();
}

export async function approveMatch(
  organization: string,
  matchId: string
) {
  const response = await fetch(
    `${API_BASE_URL}/matches/${matchId}/approve/`,
    {
      method: "POST",
      headers: {
        "X-Organization": organization,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      error?.detail || "Failed to approve match"
    );
  }

  return response.json();
}

export async function rejectMatch(
  organization: string,
  matchId: string
) {
  const response = await fetch(
    `${API_BASE_URL}/matches/${matchId}/reject/`,
    {
      method: "POST",
      headers: {
        "X-Organization": organization,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      error?.detail || "Failed to reject match"
    );
  }

  return response.json();
}

export async function ignoreTransaction(
  organization: string,
  transactionId: string
) {
  const response = await fetch(
    `${API_BASE_URL}/transactions/${transactionId}/ignore/`,
    {
      method: "POST",
      headers: {
        "X-Organization": organization,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      error?.detail || "Failed to ignore transaction"
    );
  }

  return response.json();
}