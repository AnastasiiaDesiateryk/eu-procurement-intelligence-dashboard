import React from "react";

type Props = { label: string; value: string | number; hint?: string };

export default function KPI({ label, value, hint }: Props) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {hint && <div className="kpi-hint">{hint}</div>}
    </div>
  );
}
