interface StatusBarProps {
  left: React.ReactNode;
  mid?: React.ReactNode;
  right?: React.ReactNode;
}

export default function StatusBar({ left, mid, right }: StatusBarProps) {
  return (
    <div className="status-bar">
      <div className="grow">{left}</div>
      {mid && <div>{mid}</div>}
      {right && <div>{right}</div>}
    </div>
  );
}
