import { useEffect, useState } from "react";
import { getOrganizations, getLineItems } from "./api";

function formatMoney(amount: string | number) {
  const num = Number(amount) || 0;
  return "$" + num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function App() {
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [selectedOrganization, setSelectedOrganization] = useState("");
  const [lineItems, setLineItems] = useState<any[]>([]);

  useEffect(() => {
    getOrganizations()
      .then((data) => {
        setOrganizations(data);
        if (data.length > 0) {
          setSelectedOrganization(data[0].slug);
        }
      })
      .catch((error) => {
        console.error("Error fetching organizations:", error);
      });
  }, []);

  useEffect(() => {
    if (!selectedOrganization) return;

    getLineItems(selectedOrganization)
      .then((data) => {
        setLineItems(data);
      })
      .catch((error) => {
        console.error("Error fetching line items:", error);
      });
  }, [selectedOrganization]);

  return (
    <div className="container py-4">
      {/* Header & Organization Switcher */}
      <div className="d-flex justify-content-between align-items-center bg-white p-3 border rounded shadow-sm mb-4">
        <div>
          <h2 className="h4 mb-0 fw-bold text-primary">AlphaRecon</h2>
          <small className="text-muted">Capital Call Bank Reconciliation Portal</small>
        </div>

        <div className="d-flex align-items-center gap-2">
          <label className="fw-semibold text-secondary mb-0">Organization:</label>
          <select
            className="form-select form-select-sm"
            style={{ width: "220px" }}
            value={selectedOrganization}
            onChange={(e) => setSelectedOrganization(e.target.value)}
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.slug}>
                {org.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Capital Call Line Items Panel */}
      <div className="card shadow-sm mb-4">
        <div className="card-header bg-white py-3">
          <h5 className="card-title mb-0 fw-bold">Capital Call Line Items</h5>
        </div>
        <div className="card-body p-0">
          {lineItems.length === 0 ? (
            <div className="p-4 text-center text-muted">
              No line items found for this organization.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-striped table-hover align-middle mb-0">
                <thead className="table-light">
                  <tr>
                    <th>Reference</th>
                    <th>Investor Entity</th>
                    <th>Call #</th>
                    <th>Called</th>
                    <th>Funded</th>
                    <th>Remaining</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {lineItems.map((item) => (
                    <tr key={item.id}>
                      <td className="fw-bold">{item.expected_reference}</td>
                      <td>{item.investor_name}</td>
                      <td>#{item.capital_call_number}</td>
                      <td>{formatMoney(item.amount_called)}</td>
                      <td>{formatMoney(item.amount_funded)}</td>
                      <td className={Number(item.remaining) > 0 ? "fw-bold text-warning-emphasis" : "fw-bold text-success"}>
                        {formatMoney(item.remaining)}
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            item.status === "funded"
                              ? "bg-success"
                              : item.status === "partially_funded"
                              ? "bg-warning text-dark"
                              : "bg-secondary"
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;