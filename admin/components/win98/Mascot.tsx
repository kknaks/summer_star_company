import Avatar from "@/components/pixel/Avatar";

export default function Mascot() {
  return (
    <div
      className="hide-mobile"
      style={{
        position: "fixed",
        right: 24,
        bottom: 60,
        zIndex: 30,
        padding: 8,
        background: "#fff",
        boxShadow:
          "inset 1px 1px 0 #404040, inset -1px -1px 0 #fff, 2px 2px 0 #000",
      }}
    >
      <div
        className="mono text-muted"
        style={{ fontSize: 12, marginBottom: 8 }}
      >
        ★ Summer Star
      </div>
      <Avatar seed="mascot-summer-star" scale={4} />
    </div>
  );
}
