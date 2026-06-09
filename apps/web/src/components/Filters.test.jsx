import React, { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { emptyFilters } from "../constants";
import { Filters } from "./Filters";


function FiltersHarness({ onSubmit = vi.fn(), onReset = vi.fn() }) {
  const [filters, setFilters] = useState(emptyFilters);
  return (
    <Filters
      filters={filters}
      onChange={setFilters}
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(filters);
      }}
      onReset={onReset}
    />
  );
}


describe("Filters", () => {
  it("affiche la pertinence uniquement avec une recherche textuelle", () => {
    render(<FiltersHarness />);

    expect(screen.queryByRole("option", { name: "Pertinence" })).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Recherche"), { target: { value: "terrain" } });
    expect(screen.getByRole("option", { name: "Pertinence" })).toBeInTheDocument();
  });

  it("transmet les nouveaux filtres lors de la soumission", () => {
    const onSubmit = vi.fn();
    render(<FiltersHarness onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Classe DPE"), { target: { value: "D" } });
    fireEvent.change(screen.getByLabelText("Ancienneté"), { target: { value: "7" } });
    fireEvent.change(screen.getByLabelText("Présence d’une parcelle"), { target: { value: "true" } });
    fireEvent.change(screen.getByLabelText("Surface cadastrale minimale"), { target: { value: "300" } });
    fireEvent.click(screen.getByRole("button", { name: "Filtrer" }));

    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
      energy_class: "D",
      recent_days: "7",
      has_parcel: "true",
      parcel_surface_min: "300",
    }));
  });
});
