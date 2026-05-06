interface MenuBarProps {
  items: string[];
}

export default function MenuBar({ items }: MenuBarProps) {
  return (
    <div className="menu-bar">
      {items.map((m, i) => (
        <div key={i} className="menu-item">
          <u>{m[0]}</u>
          {m.slice(1)}
        </div>
      ))}
    </div>
  );
}
