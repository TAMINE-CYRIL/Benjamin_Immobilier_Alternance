import { afterEach, describe, expect, it, vi } from "vitest";

import { removeMember, searchAnnonces, updateAnnonceTracking } from "./api";


describe("searchAnnonces", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("ignore les filtres vides et encode les nouveaux paramètres", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ items: [], total: 0, page: 1, page_size: 25 }),
    });

    await searchAnnonces({
      query: "terrain aix",
      energy_class: "D",
      recent_days: "7",
      has_parcel: "true",
      business_status: "contacted",
      is_favorite: "true",
      score_max: "",
    });

    const [url] = fetchMock.mock.calls[0];
    const query = new URL(url, "http://localhost").searchParams;
    expect(query.get("query")).toBe("terrain aix");
    expect(query.get("energy_class")).toBe("D");
    expect(query.get("recent_days")).toBe("7");
    expect(query.get("has_parcel")).toBe("true");
    expect(query.get("business_status")).toBe("contacted");
    expect(query.get("is_favorite")).toBe("true");
    expect(query.has("score_max")).toBe(false);
  });
});

describe("updateAnnonceTracking", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("envoie une requête PATCH vers le suivi de l'annonce", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ id: 7, business_status: "contacted", is_favorite: true }),
    });

    await updateAnnonceTracking(7, { business_status: "contacted", is_favorite: true });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/annonces/7/tracking",
      expect.objectContaining({
        method: "PATCH",
        credentials: "include",
        body: JSON.stringify({ business_status: "contacted", is_favorite: true }),
      })
    );
  });
});

describe("removeMember", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("envoie une requête DELETE vers le membre ciblé", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ ok: true }),
    });

    await removeMember(42);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/members/42",
      expect.objectContaining({ method: "DELETE", credentials: "include" })
    );
  });
});
