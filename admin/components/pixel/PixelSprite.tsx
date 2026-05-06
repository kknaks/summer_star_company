interface PixelSpriteProps {
  map: string[];
  palette: Record<string, string | null>;
  scale?: number;
  className?: string;
}

export default function PixelSprite({
  map,
  palette,
  scale = 4,
  className = "",
}: PixelSpriteProps) {
  const cols = map[0]?.length ?? 0;
  const rows = map.length;

  const cells: React.ReactNode[] = [];
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const c = map[y][x];
      const color = palette[c] ?? "transparent";
      cells.push(
        <div
          key={`${x}-${y}`}
          style={{
            gridColumn: x + 1,
            gridRow: y + 1,
            background: color,
            width: scale,
            height: scale,
          }}
        />,
      );
    }
  }

  return (
    <div
      className={`avatar-grid ${className}`}
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(${cols}, ${scale}px)`,
        gridTemplateRows: `repeat(${rows}, ${scale}px)`,
        width: cols * scale,
        height: rows * scale,
      }}
    >
      {cells}
    </div>
  );
}
