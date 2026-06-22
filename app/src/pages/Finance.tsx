import React, { useEffect, useMemo, useState } from "react";

/* ---------- Types ---------- */
type FinRow = {
  country: string;
  year: number;
  awards: number | null;
  spend_eur: number | null;
  avg_award_eur: number | null;
  median_award_eur: number | null;
};

type TopCPV = {
  cpv_code: string | null;
  cpv_name: string | null;
  awards: number;
  spend_eur: number;
  rnk: number;
};

type TopSupplier = {
  supplier: string;
  awards: number;
  spend_eur: number;
  rnk: number;
};
type TopBuyer = {
  buyer: string;
  awards: number;
  spend_eur: number;
  rnk: number;
};

type TltRow = {
  country: string;
  avg_tlt_days: number; // средний |award_date - dispatch_date|, дней
  lines: number;
};

/* ---------- Utils ---------- */
const items = <T,>(d: any): T[] => (Array.isArray(d) ? d : d?.items ?? []);
const money = (x?: number | null) =>
  x == null || Number.isNaN(Number(x))
    ? "—"
    : Number(x).toLocaleString(undefined, { maximumFractionDigits: 0 });
const num = (x?: number | null, d = 1) =>
  x == null || Number.isNaN(Number(x)) ? "—" : Number(x).toFixed(d);

function splitByYear(rows: FinRow[]) {
  const by20 = rows
    .filter((r) => r.year === 2020)
    .sort((a, b) => (b.spend_eur ?? 0) - (a.spend_eur ?? 0));
  const by23 = rows
    .filter((r) => r.year === 2023)
    .sort((a, b) => (b.spend_eur ?? 0) - (a.spend_eur ?? 0));
  return { y2020: by20, y2023: by23 };
}

/* ---------- Component ---------- */
export default function Finance() {
  // агрегаты по странам (buyer/supplier) для таблиц top-20
  const [buyerAgg, setBuyerAgg] = useState<FinRow[]>([]);
  const [supplierAgg, setSupplierAgg] = useState<FinRow[]>([]);
  const [loadingAgg, setLoadingAgg] = useState(true);
  const [errAgg, setErrAgg] = useState<string | null>(null);

  // карточки TLT
  const [top2020, setTop2020] = useState<TltRow[]>([]);
  const [top2023, setTop2023] = useState<TltRow[]>([]);

  // контекст для топ-10 блоков
  const [role, setRole] = useState<"buyer" | "supplier">("buyer");
  const [year, setYear] = useState<number>(2023);
  const [country, setCountry] = useState<string>("");

  // данные для топ-10
  const [topCPV, setTopCPV] = useState<TopCPV[]>([]);
  const [topSuppliers, setTopSuppliers] = useState<TopSupplier[]>([]);
  const [topBuyers, setTopBuyers] = useState<TopBuyer[]>([]);

  /* ----- Load base aggregates for tables & to seed country ----- */
  useEffect(() => {
    setLoadingAgg(true);
    setErrAgg(null);
    Promise.all([
      fetch("/api/finance/buyer?years=2020,2023").then((r) => r.json()),
      fetch("/api/finance/supplier?years=2020,2023").then((r) => r.json()),
    ])
      .then(([b, s]) => {
        const bRows = items<FinRow>(b);
        const sRows = items<FinRow>(s);
        setBuyerAgg(bRows);
        setSupplierAgg(sRows);

        // инициализируем страну: топ по spend из текущей роли/года
        const by = role === "buyer" ? splitByYear(bRows) : splitByYear(sRows);
        const list = year === 2020 ? by.y2020 : by.y2023;
        if (list.length) setCountry(list[0].country);
      })
      .catch((e) => setErrAgg(String(e)))
      .finally(() => setLoadingAgg(false));
  }, []); // initial load

  // вычисления для таблиц
  const buyerBy = useMemo(() => splitByYear(buyerAgg), [buyerAgg]);
  const supplierBy = useMemo(() => splitByYear(supplierAgg), [supplierAgg]);

  /* ----- Load TLT cards ----- */
  useEffect(() => {
    Promise.all([
      fetch("/api/tlt/top?year=2020&limit=3").then((r) => r.json()),
      fetch("/api/tlt/top?year=2023&limit=3").then((r) => r.json()),
    ])
      .then(([a, b]) => {
        setTop2020(Array.isArray(a) ? a : a?.items ?? []);
        setTop2023(Array.isArray(b) ? b : b?.items ?? []);
      })
      .catch(() => {
        setTop2020([]);
        setTop2023([]);
      });
  }, []);

  /* ----- When context changes, (re)load Top-10 lists ----- */
  useEffect(() => {
    if (!country || !year) return;

    const cpvPromise = fetch(
      `/api/finance/buyer/top_cpv?country=${encodeURIComponent(
        country
      )}&year=${year}&limit=10`
    ).then((r) => r.json());

    const rolePromise =
      role === "buyer"
        ? fetch(
            `/api/finance/buyer/top_suppliers?country=${encodeURIComponent(
              country
            )}&year=${year}&limit=10`
          ).then((r) => r.json())
        : fetch(
            `/api/finance/supplier/top_buyers?country=${encodeURIComponent(
              country
            )}&year=${year}&limit=10`
          ).then((r) => r.json());

    Promise.all([cpvPromise, rolePromise])
      .then(([cpv, list]) => {
        setTopCPV(items<TopCPV>(cpv));
        if (role === "buyer") {
          setTopSuppliers(items<TopSupplier>(list));
          setTopBuyers([]);
        } else {
          setTopBuyers(items<TopBuyer>(list));
          setTopSuppliers([]);
        }
      })
      .catch(() => {
        setTopCPV([]);
        setTopSuppliers([]);
        setTopBuyers([]);
      });
  }, [role, country, year]);

  /* ----- Options for country select based on role & year ----- */
  const countriesForContext = useMemo(() => {
    const by = role === "buyer" ? buyerBy : supplierBy;
    const list = year === 2020 ? by.y2020 : by.y2023;
    return list.map((r) => r.country);
  }, [role, year, buyerBy, supplierBy]);

  useEffect(() => {
    if (countriesForContext.length && !countriesForContext.includes(country)) {
      setCountry(countriesForContext[0]);
    }
  }, [countriesForContext]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ---------- Render ---------- */
  return (
    <div className="page">
      <h2>Tender Lead Time</h2>

      {/* KPI: two cards — Top-3 countries with minimum TLT */}
      <div
        className="grid"
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 24,
          marginBottom: 32,
        }}
      >
        <div className="card">
          <h3>Top-3 minimum TLT — 2020</h3>
          <div className="table1">
            <div className="row header">
              <div style={{ width: 36, textAlign: "left" }}>№</div>
              <div>Country</div>
              <div style={{ textAlign: "right" }}>Days</div>
              <div style={{ textAlign: "right" }}>Contracts</div>
            </div>
            {top2020.map((r, i) => (
              <div className="row" key={`t20-${r.country}-${i}`}>
                <div style={{ width: 36, textAlign: "left" }}>{i + 1}</div>
                <div>{r.country}</div>
                <div style={{ textAlign: "right" }}>
                  {num(r.avg_tlt_days, 1)}
                </div>
                <div style={{ textAlign: "right" }}>{r.lines}</div>
              </div>
            ))}
            {!top2020.length && <div className="hint">Loading...</div>}
          </div>
        </div>

        <div className="card">
          <h3>Top-3 minimum TLT — 2023</h3>
          <div className="table1">
            <div className="row header">
              <div style={{ width: 36, textAlign: "left" }}>№</div>
              <div>Country</div>
              <div style={{ textAlign: "right" }}>Days</div>
              <div style={{ textAlign: "right" }}>Contracts</div>
            </div>
            {top2023.map((r, i) => (
              <div className="row" key={`t23-${r.country}-${i}`}>
                <div style={{ width: 36, textAlign: "left" }}>{i + 1}</div>
                <div>{r.country}</div>
                <div style={{ textAlign: "right" }}>
                  {num(r.avg_tlt_days, 1)}
                </div>
                <div style={{ textAlign: "right" }}>{r.lines}</div>
              </div>
            ))}
            {!top2023.length && <div className="hint">Loading...</div>}
          </div>
        </div>
      </div>

      {/* Пояснение про TLT */}
      <div className="card" style={{ marginTop: 5 }}>
        <h3>Tender Lead Time (TLT)</h3>
        <div className="hint" style={{ lineHeight: 1.5 }}>
          <b>Tender Lead Time (TLT)</b> – the number of days between the
          dispatch date (when the tender is officially published) and the award
          date (when the contract is awarded). It is an indicator of how quickly
          procurement procedures move from publication to decision. A shorter
          TLT means the process is faster and more efficient — suppliers get
          results sooner, buyers reduce administrative delays. A longer TLT
          suggests slower procedures, possibly due to complex requirements,
          legal challenges, or inefficiencies. Organizations and policymakers
          track TLT to benchmark procurement systems, improve transparency, and
          ensure public money is spent without unnecessary delays.
        </div>
      </div>

      {/* Контекст + два Top-10 списка (оставляем как было) */}
      <div className="card">
        <h3>Top-10 Categories Based on Selected Role</h3>
        <div
          className="controls"
          style={{ display: "flex", gap: 12, flexWrap: "wrap" }}
        >
          <label>Role:</label>
          <select value={role} onChange={(e) => setRole(e.target.value as any)}>
            <option value="buyer">Buyer</option>
            <option value="supplier">Supplier</option>
          </select>

          <label>Year:</label>
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          >
            <option value={2020}>2020</option>
            <option value={2023}>2023</option>
          </select>

          <label>Country:</label>
          <select value={country} onChange={(e) => setCountry(e.target.value)}>
            {countriesForContext.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <div className="hint">
            <b>CPV (Common Procurement Vocabulary)</b> is the EU system for
            classifying public procurement contracts. It standardizes categories
            of goods, services, and works. This table shows the{" "}
            <b>Top-10 CPV categories</b> and key partners (suppliers or buyers)
            for the selected country, role, and year. It supports supply chain
            strategy by highlighting spending concentration, dominant partners,
            and potential risks or dependencies.
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "2rem",
            marginTop: 12,
          }}
        >
          <div>
            <div className="kpi-label" style={{ marginBottom: 6 }}>
              Top-10 CPV — {country} ({year})
            </div>
            <div className="table">
              <div className="row header">
                <div>CPV</div>
                <div style={{ textAlign: "right" }}>Contracts</div>
                <div style={{ textAlign: "right" }}>Spend (EUR)</div>
              </div>

              {topCPV.map((x) => (
                <div className="row" key={`cpv-${x.rnk}-${x.cpv_code}`}>
                  <div style={{ maxWidth: 520 }}>
                    <div style={{ fontWeight: 600 }}>{x.cpv_name ?? "—"}</div>
                    <div className="hint" style={{ opacity: 0.8 }}>
                      {x.cpv_code ?? ""}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>{num(x.awards, 0)}</div>
                  <div style={{ textAlign: "right" }}>{money(x.spend_eur)}</div>
                </div>
              ))}

              {!topCPV.length && <div className="hint">Loading...</div>}
            </div>{" "}
            {/* ← закрыли .table */}
          </div>{" "}
          {/* ← закрыли левую колонку */}
          {role === "buyer" ? (
            <div>
              <div className="kpi-label" style={{ marginBottom: 6 }}>
                Top-10 suppliers — {country} ({year})
              </div>
              <div className="table">
                <div className="row header">
                  <div>Supplier</div>
                  <div style={{ textAlign: "right" }}>Contracts</div>
                  <div style={{ textAlign: "right" }}>Spend (EUR)</div>
                </div>
                {topSuppliers.map((x) => (
                  <div className="row" key={`sup-${x.rnk}-${x.supplier}`}>
                    <div>{x.supplier}</div>
                    <div style={{ textAlign: "right" }}>{num(x.awards, 0)}</div>
                    <div style={{ textAlign: "right" }}>
                      {money(x.spend_eur)}
                    </div>
                  </div>
                ))}
                {!topSuppliers.length && <div className="hint">Loading...</div>}
              </div>
            </div>
          ) : (
            <div>
              <div className="kpi-label" style={{ marginBottom: 6 }}>
                Top-10 buyers — {country} ({year})
              </div>
              <div className="table">
                <div className="row header">
                  <div>Buyer</div>
                  <div style={{ textAlign: "right" }}>Contracts</div>
                  <div style={{ textAlign: "right" }}>Spend (EUR)</div>
                </div>
                {topBuyers.map((x) => (
                  <div className="row" key={`buy-${x.rnk}-${x.buyer}`}>
                    <div>{x.buyer}</div>
                    <div style={{ textAlign: "right" }}>{num(x.awards, 0)}</div>
                    <div style={{ textAlign: "right" }}>
                      {money(x.spend_eur)}
                    </div>
                  </div>
                ))}
                {!topBuyers.length && <div className="hint">Loading...</div>}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Таблицы Top-20 по странам — оставляем как было */}
      <div className="card">
        <h3>Buyer countries — Top-10 (Spend / Average / Median)</h3>
        {loadingAgg && <div className="hint">Loading…</div>}
        {errAgg && <div className="error">Error: {errAgg}</div>}
        {!loadingAgg && !errAgg && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "2rem",
            }}
          >
            <div>
              <div className="kpi-label" style={{ marginBottom: 8 }}>
                2020
              </div>
              <div className="table">
                <div className="row header">
                  <div>Country</div>
                  <div style={{ textAlign: "right" }}>Spend (EUR)</div>
                  <div style={{ textAlign: "right" }}>Avg (EUR)</div>
                  <div style={{ textAlign: "right" }}>Median (EUR)</div>
                </div>
                {buyerBy.y2020.slice(0, 10).map((r) => (
                  <div className="row" key={`b20-${r.country}`}>
                    <div>{r.country}</div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.spend_eur)}
                    </div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.avg_award_eur)}
                    </div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.median_award_eur)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="kpi-label" style={{ marginBottom: 8 }}>
                2023
              </div>
              <div className="table">
                <div className="row header">
                  <div>Country</div>
                  <div style={{ textAlign: "right" }}>Spend (EUR)</div>
                  <div style={{ textAlign: "right" }}>Avg (EUR)</div>
                  <div style={{ textAlign: "right" }}>Median (EUR)</div>
                </div>
                {buyerBy.y2023.slice(0, 10).map((r) => (
                  <div className="row" key={`b23-${r.country}`}>
                    <div>{r.country}</div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.spend_eur)}
                    </div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.avg_award_eur)}
                    </div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.median_award_eur)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <h3>Supplier countries — Top-10 (Spend / Average / Median)</h3>
        {loadingAgg && <div className="hint">Loading…</div>}
        {errAgg && <div className="error">Error: {errAgg}</div>}
        {!loadingAgg && !errAgg && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "2rem",
            }}
          >
            <div>
              <div className="kpi-label" style={{ marginBottom: 8 }}>
                2020
              </div>
              <div className="table">
                <div className="row header">
                  <div>Country</div>
                  <div style={{ textAlign: "right" }}>Spend (EUR)</div>
                  <div style={{ textAlign: "right" }}>Avg (EUR)</div>
                  <div style={{ textAlign: "right" }}>Median (EUR)</div>
                </div>
                {supplierBy.y2020.slice(0, 10).map((r) => (
                  <div className="row" key={`s20-${r.country}`}>
                    <div>{r.country}</div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.spend_eur)}
                    </div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.avg_award_eur)}
                    </div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.median_award_eur)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="kpi-label" style={{ marginBottom: 8 }}>
                2023
              </div>
              <div className="table">
                <div className="row header">
                  <div>Country</div>
                  <div style={{ textAlign: "right" }}>Spend (EUR)</div>
                  <div style={{ textAlign: "right" }}>Avg (EUR)</div>
                  <div style={{ textAlign: "right" }}>Median (EUR)</div>
                </div>
                {supplierBy.y2023.slice(0, 10).map((r) => (
                  <div className="row" key={`s23-${r.country}`}>
                    <div>{r.country}</div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.spend_eur)}
                    </div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.avg_award_eur)}
                    </div>
                    <div style={{ textAlign: "right" }}>
                      {money(r.median_award_eur)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
