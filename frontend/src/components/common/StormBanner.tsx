import Button from "./Button";

interface StormBannerProps {
  isSevere: boolean;
  summary: string;
  onAction?: () => void;
}

export default function StormBanner({ isSevere, summary, onAction }: StormBannerProps) {
  return (
    <div className={`storm-banner ${isSevere ? "severe" : "safe"}`}>
      <div>
        <strong>{isSevere ? "Storm Mode Active" : "All Clear"}</strong>
        <div className="page-subtitle">{summary}</div>
      </div>
      {onAction ? (
        <Button variant={isSevere ? "danger" : "secondary"} onClick={onAction}>
          {isSevere ? "Review Outreach" : "Trigger Weather Check"}
        </Button>
      ) : null}
    </div>
  );
}
