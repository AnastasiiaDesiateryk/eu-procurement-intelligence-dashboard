import React, { useEffect, useMemo, useState } from "react";

type Row = {
  supplier: string;
  otd_pct: number;
  otif_pct: number;
  podr_pct: number;
  lt_avg: number;
  lt_cov: number;
  lines: number;
};

export default function Suppliers() {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<keyof Row>("podr_pct");

  useEffect(() => {
    fetch("/api/suppliers")
      .then((r) => r.json())
      .then((d) => setRows(d.items ?? []))
      .finally(() => setLoading(false));
  }, []);

  const sorted = useMemo(() => {
    return [...rows].sort(
      (a, b) => (Number(b[sortBy]) || 0) - (Number(a[sortBy]) || 0)
    );
  }, [rows, sortBy]);

  if (loading) return <div className="page">Loading…</div>;

  return (
    <div className="page">
      <h2>Suppliers</h2>
      <div className="card">
        <div className="toolbar">
          <label>Sort by:&nbsp;</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as keyof Row)}
          >
            <option value="podr_pct">PODR %</option>
            <option value="otif_pct">OTIF %</option>
            <option value="otd_pct">OTD %</option>
            <option value="lt_avg">LT avg</option>
            <option value="lt_cov">LT CoV</option>
            <option value="lines">Lines</option>
          </select>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Supplier</th>
              <th>OTD %</th>
              <th>OTIF %</th>
              <th>PODR %</th>
              <th>LT avg</th>
              <th>LT CoV</th>
              <th>Lines</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={r.supplier}>
                <td>{r.supplier}</td>
                <td>{r.otd_pct?.toFixed?.(1)}</td>
                <td>{r.otif_pct?.toFixed?.(1)}</td>
                <td>{r.podr_pct?.toFixed?.(1)}</td>
                <td>{r.lt_avg?.toFixed?.(2)}</td>
                <td>{r.lt_cov?.toFixed?.(3)}</td>
                <td>{r.lines}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <small>
          Клик по строке можно расширить до тренда поставщика позже.
        </small>
      </div>
    </div>
  );
}
