import AppShell from "../components/common/AppShell";
import Button from "../components/common/Button";
import PageHeader from "../components/common/PageHeader";
import StatCard from "../components/common/StatCard";
import StormBanner from "../components/common/StormBanner";

export default function DashboardPage() {
  return (
    <AppShell>
      <div>
        <PageHeader
          title="Dashboard"
          subtitle="Today's referral load, storm risk, and outreach activity."
          actions={<Button>New Referral</Button>}
        />
        <StormBanner
          isSevere={false}
          summary="Snowfall below threshold. Next automated check in 30 minutes."
          onAction={() => {}}
        />
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 16,
          }}
        >
          <StatCard label="Active referrals" value="18" helper="+2 since yesterday" />
          <StatCard label="Overdue follow-ups" value="3" helper="Needs review" />
          <StatCard label="High-risk patients" value="12" helper="Storm contact list" />
          <StatCard label="Weather alerts" value="0" helper="No warnings" />
        </div>
      </div>
    </AppShell>
  );
}
