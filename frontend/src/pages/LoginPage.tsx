import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Button from "../components/common/Button";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await login(username.trim(), password.trim());
      navigate("/", { replace: true });
    } catch {
      setError("Invalid username or password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card card">
        <div className="login-header">
          <h1>ClearCare</h1>
          <p>Nurse Console</p>
        </div>
        <form onSubmit={handleSubmit} className="form-body">
          {error ? <div className="form-error">{error}</div> : null}
          <label className="form-field">
            <span>Username</span>
            <input
              type="text"
              placeholder="e.g. nurse.adams"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="form-field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          <Button
            type="submit"
            variant="primary"
            disabled={!username.trim() || !password.trim() || submitting}
          >
            {submitting ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </div>
    </div>
  );
}
