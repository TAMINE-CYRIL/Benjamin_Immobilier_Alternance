import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DetailPanel } from "./DetailPanel";


describe("DetailPanel scoring", () => {
  it("affiche les composantes, la confiance et les raisons du score", () => {
    render(
      <DetailPanel
        loading={false}
        onClose={() => {}}
        annonce={{
          id: 1,
          title: "Terrain à potentiel",
          score: 76,
          score_confidence: 82,
          score_risk_level: "medium",
          score_version: "2.1",
          score_details: {
            components: {
              market_discount: 34,
              land_potential: 25,
              liquidity: 8,
              listing_signals: 7,
              energy: 2,
            },
            reasons: ["Prix au m² inférieur de 18 % à la médiane DVF"],
            risks: ["Une servitude détectée"],
          },
        }}
      />,
    );

    expect(screen.getByText("76 / 100")).toBeInTheDocument();
    expect(screen.getByText("Confiance : 82 %")).toBeInTheDocument();
    expect(screen.getByText("Prix et décote")).toBeInTheDocument();
    expect(screen.getByText("Prix au m² inférieur de 18 % à la médiane DVF")).toBeInTheDocument();
    expect(screen.getByText("Une servitude détectée")).toBeInTheDocument();
  });
});
