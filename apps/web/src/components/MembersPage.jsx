import React, { useEffect, useState } from "react";
import { inviteMember, listMembers, removeMember } from "../api";

export function MembersPage({ currentUserId }) {
  const [memberEmail, setMemberEmail] = useState("");
  const [memberLoading, setMemberLoading] = useState(false);
  const [memberMessage, setMemberMessage] = useState("");
  const [memberError, setMemberError] = useState("");
  const [members, setMembers] = useState([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [removingMemberId, setRemovingMemberId] = useState(null);

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

  async function handleRemoveMember(member) {
    const confirmed = window.confirm(
      `Retirer l'accès de ${member.email} ? Cette personne ne pourra plus se connecter.`
    );
    if (!confirmed) {
      return;
    }

    setRemovingMemberId(member.id);
    setMemberMessage("");
    setMemberError("");

    try {
      await removeMember(member.id);
      await loadMembers();
      setMemberMessage(`L'accès de ${member.email} a été retiré.`);
    } catch (err) {
      setMemberError(err.message);
    } finally {
      setRemovingMemberId(null);
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
            <div className="member-actions">
              <small>{member.id === currentUserId ? "Vous" : "Actif"}</small>
              {member.id !== currentUserId ? (
                <button
                  className="danger-button"
                  type="button"
                  disabled={removingMemberId !== null}
                  onClick={() => handleRemoveMember(member)}
                >
                  {removingMemberId === member.id ? "Retrait..." : "Retirer"}
                </button>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
