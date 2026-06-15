import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { inviteMember, listMembers, removeMember } from "../api";
import { MembersPage } from "./MembersPage";

vi.mock("../api", () => ({
  inviteMember: vi.fn(),
  listMembers: vi.fn(),
  removeMember: vi.fn(),
}));

describe("MembersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    inviteMember.mockResolvedValue({});
    removeMember.mockResolvedValue({ ok: true });
    listMembers
      .mockResolvedValueOnce({
        items: [
          { id: 1, email: "one@example.com", is_active: true },
          { id: 2, email: "two@example.com", is_active: true },
        ],
      })
      .mockResolvedValueOnce({
        items: [{ id: 1, email: "one@example.com", is_active: true }],
      });
  });

  it("retire un membre après confirmation et recharge la liste", async () => {
    render(<MembersPage currentUserId={1} />);

    await screen.findByText("two@example.com");
    fireEvent.click(screen.getByRole("button", { name: "Retirer" }));

    await waitFor(() => expect(removeMember).toHaveBeenCalledWith(2));
    await screen.findByText("L'accès de two@example.com a été retiré.");
    expect(listMembers).toHaveBeenCalledTimes(2);
  });

  it("ne propose pas de retirer le compte connecté", async () => {
    render(<MembersPage currentUserId={1} />);

    await screen.findByText("one@example.com");
    expect(screen.getByText("Vous")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Retirer" })).toHaveLength(1);
  });
});
