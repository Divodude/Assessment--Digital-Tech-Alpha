import { useEffect, useState } from "react";
import {
  getOrganizations,
  getLineItems,
  getTransactions,
  importBankStatement,
  approveMatch,
  rejectMatch,
  ignoreTransaction,
} from "./api";

function formatMoney(amount: string | number) {
  const num = Number(amount) || 0;
  return "$" + num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function App() {
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [selectedOrganization, setSelectedOrganization] = useState("");
  const [lineItems, setLineItems] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);

  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSummary, setUploadSummary] = useState<any>(null);
  const [uploadError, setUploadError] = useState("");

  const [actionLoading, setActionLoading] = useState(false);

  // helper function to load all data for current org
  function loadData(orgSlug: string) {
    if (!orgSlug) return;

    getLineItems(orgSlug)
      .then((data) => setLineItems(data))
      .catch((err) => console.log("line items error", err));

    getTransactions(orgSlug)
      .then((data) => setTransactions(data))
      .catch((err) => console.log("transactions error", err));
  }

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
    setUploadSummary(null);
    setUploadError("");
    loadData(selectedOrganization);
  }, [selectedOrganization]);

  function handleUpload() {
    if (!selectedFile) {
      alert("Please select a CSV file first!");
      return;
    }

    setIsUploading(true);
    setUploadError("");
    setUploadSummary(null);

    importBankStatement(selectedOrganization, selectedFile)
      .then((res) => {
        console.log("Upload result:", res);
        setUploadSummary(res);
        setIsUploading(false);
        loadData(selectedOrganization);
      })
      .catch((err) => {
        console.error("Upload failed:", err);
        setUploadError(err.message || "Failed to upload file");
        setIsUploading(false);
      });
  }

  // approve a proposed match
  function handleApprove(matchId: string) {
    if (!window.confirm("Approve this match and update capital call funding?")) {
      return;
    }

    setActionLoading(true);
    approveMatch(selectedOrganization, matchId)
      .then(() => {
        alert("Match approved successfully!");
        loadData(selectedOrganization);
        setActionLoading(false);
      })
      .catch((err) => {
        console.log("Approve error:", err);
        alert(err.message || "Could not approve match");
        setActionLoading(false);
      });
  }

  // reject a proposed match
  function handleReject(matchId: string) {
    setActionLoading(true);
    rejectMatch(selectedOrganization, matchId)
      .then(() => {
        loadData(selectedOrganization);
        setActionLoading(false);
      })
      .catch((err) => {
        console.log("Reject error:", err);
        alert(err.message || "Could not reject match");
        setActionLoading(false);
      });
  }

  // ignore a transaction
  function handleIgnore(txnId: string) {
    setActionLoading(true);
    ignoreTransaction(selectedOrganization, txnId)
      .then(() => {
        loadData(selectedOrganization);
        setActionLoading(false);
      })
      .catch((err) => {
        console.log("Ignore error:", err);
        alert(err.message || "Could not ignore transaction");
        setActionLoading(false);
      });
  }

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

      {/* CSV Upload Section */}
      <div className="card shadow-sm mb-4">
        <div className="card-header bg-white py-3">
          <h5 className="card-title mb-0 fw-bold">Import Bank Statement (CSV)</h5>
        </div>
        <div className="card-body">
          <div className="row g-2 align-items-center">
            <div className="col-auto flex-grow-1">
              <input
                type="file"
                className="form-control"
                accept=".csv"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />
            </div>
            <div className="col-auto">
              <button
                className="btn btn-primary"
                onClick={handleUpload}
                disabled={isUploading || !selectedFile}
              >
                {isUploading ? "Uploading..." : "Upload CSV"}
              </button>
            </div>
          </div>

          {/* Upload error banner if any */}
          {uploadError && (
            <div className="alert alert-danger mt-3 mb-0" role="alert">
              <strong>Error: </strong> {uploadError}
            </div>
          )}

          {/* Upload summary display */}
          {uploadSummary && (
            <div className="alert alert-info mt-3 mb-0">
              <h6 className="fw-bold mb-2">Import Summary:</h6>
              <div>Rows Imported: <strong>{uploadSummary.imported}</strong></div>
              <div>Duplicates Skipped: <strong>{uploadSummary.duplicates}</strong></div>

              {uploadSummary.errors && uploadSummary.errors.length > 0 && (
                <div className="mt-2 text-danger">
                  <strong>Errors found ({uploadSummary.errors.length}):</strong>
                  <ul className="mb-0 mt-1 ps-3">
                    {uploadSummary.errors.map((err: any, idx: number) => (
                      <li key={idx}>
                        Line {err.line}: {err.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
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

      {/* Bank Transactions Table */}
      <div className="card shadow-sm mb-4">
        <div className="card-header bg-white py-3">
          <h5 className="card-title mb-0 fw-bold">Bank Transactions</h5>
        </div>
        <div className="card-body p-0">
          {transactions.length === 0 ? (
            <div className="p-4 text-center text-muted">
              No bank transactions found. Upload a bank statement CSV to get started.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-striped table-hover align-middle mb-0">
                <thead className="table-light">
                  <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Bank Ref</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Suggested Match</th>
                    <th>Match Reason</th>
                    <th style={{ minWidth: "150px" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((txn) => {
                    const proposedMatches = txn.matches?.filter(
                      (m: any) => m.status === "proposed"
                    ) || [];

                    return (
                      <tr key={txn.id}>
                        <td>{txn.date}</td>
                        <td style={{ maxWidth: "220px" }}>{txn.description}</td>
                        <td><small className="text-muted font-monospace">{txn.reference}</small></td>
                        <td className={Number(txn.amount) < 0 ? "text-danger fw-bold" : "text-success fw-bold"}>
                          {formatMoney(txn.amount)}
                        </td>
                        <td>
                          <span
                            className={`badge ${
                              txn.status === "suggested"
                                ? "bg-info text-dark"
                                : txn.status === "needs_review"
                                ? "bg-warning text-dark"
                                : txn.status === "reconciled"
                                ? "bg-success"
                                : "bg-secondary"
                            }`}
                          >
                            {txn.status}
                          </span>
                        </td>
                        <td>
                          {txn.suggested_investor ? (
                            <div>
                              <strong>{txn.suggested_investor}</strong>
                              <div className="text-muted small">{txn.suggested_reference}</div>
                            </div>
                          ) : (
                            <span className="text-muted">—</span>
                          )}
                        </td>
                        <td style={{ maxWidth: "280px", fontSize: "13px" }}>
                          {txn.reason || <span className="text-muted">—</span>}
                        </td>
                        <td>
                          {/* If reconciled */}
                          {txn.status === "reconciled" && (
                            <span className="badge bg-success">Reconciled</span>
                          )}

                          {/* If ignored */}
                          {txn.status === "ignored" && (
                            <span className="text-muted small">Ignored</span>
                          )}

                          {/* Proposed matches approve / reject buttons */}
                          {proposedMatches.map((m: any) => (
                            <div key={m.id} className="d-flex gap-1 mb-1">
                              <button
                                className="btn btn-sm btn-success py-0 px-2"
                                disabled={actionLoading}
                                onClick={() => handleApprove(m.id)}
                              >
                                Approve
                              </button>
                              <button
                                className="btn btn-sm btn-outline-danger py-0 px-2"
                                disabled={actionLoading}
                                onClick={() => handleReject(m.id)}
                              >
                                Reject
                              </button>
                            </div>
                          ))}

                          {/* Ignore button for suggested or needs_review */}
                          {(txn.status === "suggested" || txn.status === "needs_review") && (
                            <button
                              className="btn btn-sm btn-outline-secondary py-0 px-2"
                              disabled={actionLoading}
                              onClick={() => handleIgnore(txn.id)}
                            >
                              Ignore
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
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