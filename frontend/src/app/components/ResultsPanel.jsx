import React from "react";
import "./ResultsPanel.css";
import KpiCards from "./KpiCards";
import ChartView from "./ChartView";
import DataTable from "./DataTable";

function ResultsPanel({ result }) {
  const isEmpty =
    !result.chart &&
    (!result.table || result.table.length === 0) &&
    (!result.kpis || Object.keys(result.kpis).length === 0);

  return (
    <div className="results-panel">
      <div className="results-panel__card">
        <h3>Resumen</h3>
        <p>{result.message}</p>
      </div>

      {isEmpty ? (
        <div className="results-panel__empty">
          <h3>Todavía no hay resultados</h3>
          <p>Haz una consulta en el chat para ver métricas, gráficos y tablas analíticas.</p>
        </div>
      ) : (
        <>
          <KpiCards kpis={result.kpis} />
          <ChartView chart={result.chart} />
          <DataTable rows={result.table} />
        </>
      )}
    </div>
  );
}

export default ResultsPanel;