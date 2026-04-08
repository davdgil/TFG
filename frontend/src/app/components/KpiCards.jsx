import React from "react";
import "./KpiCards.css";

function KpiCards({ kpis }) {
  const entries = Object.entries(kpis || {});
  if (entries.length === 0) return null;

  return (
    <div className="kpi-cards">
      {entries.map(([key, value]) => (
        <div key={key} className="kpi-cards__card">
          <div className="kpi-cards__label">{key}</div>
          <div className="kpi-cards__value">{value}</div>
        </div>
      ))}
    </div>
  );
}

export default KpiCards;