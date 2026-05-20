import React, { useEffect, useState } from "react";
import { inviteMember, listMembers } from "../api";

export function MembersPage() {
  const [memberEmail, setMemberEmail] = useState("");
  const [memberLoading, setMemberLoading] = useState(false);
  const [memberMessage, setMemberMessage] = useState("");
  const [memberError, setMemberError] = useState("");
  const [members, setMembers] = useState([]);
  const [membersLoading, setMembersLoading] = useState(false);

  useEffect(() => {
    loadMembers();
  }, []);

  async function loadMembers() {
    setMembersLoading(true);
    try {
      const result = await listMembers();
      setMembers(result.items || []);
    } catch (err) {
      setMemberError(err.message);
    } finally {
      setMembersLoading(false);
    }
  }

  async function submitMemberInvitation(event) {
    event.preventDefault();
    const email = memberEmail.trim();

    if (!email) {
      setMemberMessage("");
      setMemberError("Renseignez une adresse e-mail.");
      return;
    }

    setMemberLoading(true);
    setMemberMessage("");
    setMemberError("");

    try {
      const result = await inviteMember(email);
      setMemberEmail("");
      await loadMembers();
      setMemberMessage(
        result.created
          ? "Invitation envoyée. Le membre pourra choisir son mot de passe par email."
          : "Invitation renvoyée à ce membre existant."
      );
    } catch (err) {
      setMemberError(err.message);
    } finally {
      setMemberLoading(false);
    }
  }

  return (
    <section className="member-panel">
      <div>
        <p className="eyebrow">Membres</p>
        <h2>Ajouter un accès</h2>
        <span className="member-count">
          {membersLoading ? "Chargement..." : `${members.length} compte(s)`}
        </span>
      </div>
      <form className="member-form" onSubmit={submitMemberInvitation}>
        <label className="member-email">
          <span>Adresse e-mail</span>
          <input
            type="email"
            autoComplete="email"
            value={memberEmail}
            onChange={(event) => setMemberEmail(event.target.value)}
            placeholder="membre@example.com"
            disabled={memberLoading}
            required
          />
        </label>
        <button type="submit" disabled={memberLoading}>
          {memberLoading ? "Envoi..." : "Envoyer l'invitation"}
        </button>
      </form>
      {memberMessage ? <span className="success-message member-feedback">{memberMessage}</span> : null}
      {memberError ? <span className="error member-feedback">{memberError}</span> : null}
      <div className="members-list">
        {members.map((member) => (
          <div className="member-row" key={member.id}>
            <span>{member.email}</span>
            <small>{member.is_active ? "Actif" : "Inactif"}</small>
          </div>
        ))}
      </div>
    </section>
  );
}
