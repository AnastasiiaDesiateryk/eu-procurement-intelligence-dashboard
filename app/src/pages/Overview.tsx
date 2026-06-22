import React, { useEffect, useState } from "react";
import KPI from "../components/KPI";
import SupersetEmbed from "../components/SupersetEmbed";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";

type MonthlyRow = {
  month: string;
  otd_pct: number;
  otif_pct: number;
  podr_pct: number;
  lt_avg: number;
  lt_cov: number;
  c2c_days?: number;
};

export default function Overview() {
  const [rows, setRows] = useState<MonthlyRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/kpi") // <- этот эндпоинт надо сделать в FastAPI
      .then((r) => r.json())
      .then((d) => setRows(d.items ?? []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page">Loading…</div>;
  if (!rows.length) return <div className="page">No data</div>;

  const last = rows[rows.length - 1];

  return (
    <div className="page">
      <h2>Overview</h2>

      <div className="grid kpis">
        <KPI label="OTD %" value={`${last.otd_pct.toFixed(1)}%`} />
        <KPI label="OTIF %" value={`${last.otif_pct.toFixed(1)}%`} />
        <KPI label="PODR %" value={`${last.podr_pct?.toFixed?.(1) ?? "—"}%`} />
        <KPI label="Lead Time (avg)" value={`${last.lt_avg.toFixed(2)} d`} />
        <KPI label="Lead Time CoV" value={last.lt_cov.toFixed(3)} />
        <KPI
          label="C2C Days"
          value={last.c2c_days ? `${last.c2c_days.toFixed(0)} d` : "—"}
          hint="из v_c2c"
        />
      </div>

      <div className="grid charts">
        <div className="card">
          <h3>Service timeline (OTD / OTIF)</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="otd_pct"
                name="OTD %"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="otif_pct"
                name="OTIF %"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3>Lead time timeline (avg / CoV)</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="lt_avg"
                name="LT avg"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="lt_cov"
                name="LT CoV"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3>Superset dashboard (embedded)</h3>
        <SupersetEmbed
          src="http://localhost:8088/superset/dashboard/SCM%20MVP/?standalone=1"
          height={700}
        />
      </div>
    </div>
  );
}
