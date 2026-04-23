import React from "react";
import { formatMoney } from "../utils";

export function AnnoncesTable({ annonces, onSelect }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Score</th>
            <th>Annonce</th>
            <th>Ville</th>
            <th>Prix</th>
            <th>Surface</th>
            <th>Prix/m2</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {annonces.map((annonce) => (
            <tr key={annonce.id} onClick={() => onSelect(annonce.id)}>
              <td><strong>{annonce.score ?? "-"}</strong></td>
              <td>{annonce.title || "Sans titre"}</td>
              <td>{[annonce.city, annonce.zip_code].filter(Boolean).join(" ") || "-"}</td>
              <td>{formatMoney(annonce.price)}</td>
              <td>{annonce.surface ? `${annonce.surface} m2` : "-"}</td>
              <td>{annonce.price_m2 ? `${Math.round(annonce.price_m2)} EUR` : "-"}</td>
              <td>{annonce.source_site || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
