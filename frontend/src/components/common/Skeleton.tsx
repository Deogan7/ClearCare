interface SkeletonProps {
  width?: string;
  height?: string;
}

export default function Skeleton({ width = "100%", height = "16px" }: SkeletonProps) {
  return <div className="skeleton" style={{ width, height }} />;
}
