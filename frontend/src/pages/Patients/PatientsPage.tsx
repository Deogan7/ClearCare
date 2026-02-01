import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/common/AppShell";
import Table from "../../components/common/Table";
import Button from "../../components/common/Button";
import { getPatients } from "../../services/patientService";
import { getReferrals } from "../../services/referralService";
import type { Patient } from "../../types/patient";
import type { Referral } from "../../types/referral";
import PatientFormModal from "./PatientFormModal";
import DeletePatientModal from "./DeletePatientModal";

type SortDir = "asc" | "desc";

export default function PatientsPage() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Patient | null>(null);
  const [search, setSearch] = useState("");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [patientResponse, referralResponse] = await Promise.all([
        getPatients(),
        getReferrals(),
      ]);
      setPatients(Array.isArray(patientResponse.data) ? patientResponse.data : []);
      setReferrals(Array.isArray(referralResponse.data) ? referralResponse.data : []);
    } catch {
      setError("Unable to load patients.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const activeReferralCounts = useMemo(() => {
    const counts = new Map<string, number>();
    if (!Array.isArray(referrals)) {
      return counts;
    }
    referrals.forEach((referral) => {
      if (referral.status !== "closed") {
        counts.set(
          referral.patient_id,
          (counts.get(referral.patient_id) ?? 0) + 1
        );
      }
    });
    return counts;
  }, [referrals]);

  const displayedPatients = useMemo(() => {
    const term = search.trim().toLowerCase();
    let list = Array.isArray(patients) ? [...patients] : [];
    if (term) {
      list = list.filter((p) =>
        `${p.first_name} ${p.last_name}`.toLowerCase().includes(term)
      );
    }
    list.sort((a, b) => {
      const cmp = `${a.last_name} ${a.first_name}`.localeCompare(
        `${b.last_name} ${b.first_name}`
      );
      return sortDir === "asc" ? cmp : -cmp;
    });
    return list;
  }, [patients, search, sortDir]);

  return (
    <AppShell>
      <div>
        <h1>Patients</h1>
        <div className="filter-bar" style={{ marginBottom: 4 }}>
          <div className="filter-group">
            <span className="filter-label">Search</span>
            <input
              className="filter-search"
              type="text"
              placeholder="Search by name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <span className="filter-label">Sort by name</span>
            <button
              type="button"
              className="sort-toggle"
              onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
            >
              {sortDir === "asc" ? "A → Z" : "Z → A"}
              <span aria-hidden>{sortDir === "asc" ? "↑" : "↓"}</span>
            </button>
          </div>
          <Button type="button" onClick={() => setIsModalOpen(true)}>
            New Patient
          </Button>
        </div>
        {loading ? <div>Loading patients...</div> : null}
        {error ? <div>{error}</div> : null}
        {!loading && !error && displayedPatients.length === 0 ? (
          <div>{search ? "No patients match your search." : "No patients found."}</div>
        ) : null}
        {!loading && !error && displayedPatients.length > 0 ? (
          <Table headers={["Name", "Phone", "High-risk flag", "Active referrals", ""]}>
              {displayedPatients.map((patient) => (
                <tr key={patient.id}>
                  <td>
                    <Button
                      type="button"
                      onClick={() => navigate(`/patients/${patient.id}`)}
                    >
                      {patient.first_name} {patient.last_name}
                    </Button>
                  </td>
                  <td>{patient.phone}</td>
                  <td>{patient.is_high_risk ? "Yes" : "No"}</td>
                  <td>{activeReferralCounts.get(patient.id) ?? 0}</td>
                  <td>
                    <Button
                      type="button"
                      variant="danger"
                      onClick={() => setDeleteTarget(patient)}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
          </Table>
        ) : null}
      </div>
      <PatientFormModal
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSaved={loadData}
      />
      <DeletePatientModal
        open={deleteTarget !== null}
        patient={deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onDeleted={loadData}
      />
    </AppShell>
  );
}
