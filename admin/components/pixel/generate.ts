import type { SpriteDef } from "./icons";

const SKIN_TONES = ["#fcb98e", "#f1a675", "#d39060", "#b8763d"];
const HAIR_COLORS = [
  "#3a2410",
  "#1a1a1a",
  "#5a3a1a",
  "#8a5a2a",
  "#cc6633",
  "#4a2470",
  "#aa4444",
];
const SHIRT_COLORS = [
  "#000080",
  "#008000",
  "#c81e1e",
  "#a040a0",
  "#005577",
  "#806000",
  "#404040",
  "#1084d0",
];
const HAT_COLORS = [
  "#c81e1e",
  "#000080",
  "#008000",
  "#4a2470",
  "#bdbd00",
  "#000000",
];

function hashStr(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = (h * 16777619) >>> 0;
  }
  return h;
}

function pick<T>(arr: T[], idx: number): T {
  const i = ((idx % arr.length) + arr.length) % arr.length;
  return arr[i];
}

function shadeColor(hex: string, percent: number): string {
  const num = parseInt(hex.replace("#", ""), 16);
  let r = (num >> 16) + Math.round((255 * percent) / 100);
  let gg = ((num >> 8) & 0x00ff) + Math.round((255 * percent) / 100);
  let b = (num & 0x0000ff) + Math.round((255 * percent) / 100);
  r = Math.max(0, Math.min(255, r));
  gg = Math.max(0, Math.min(255, gg));
  b = Math.max(0, Math.min(255, b));
  return "#" + ((r << 16) | (gg << 8) | b).toString(16).padStart(6, "0");
}

export function generateAvatar(seed: string): SpriteDef {
  const h = hashStr(String(seed));
  const skin = pick(SKIN_TONES, h);
  const hair = pick(HAIR_COLORS, h >>> 3);
  const shirt = pick(SHIRT_COLORS, h >>> 6);
  const hat = pick(HAT_COLORS, h >>> 9);
  const hasHat = (h >>> 12) % 3 === 0;
  const hasGlasses = (h >>> 14) % 2 === 0;
  const hasMustache = (h >>> 16) % 4 === 0;
  const hairStyle = (h >>> 18) % 3;
  const shirtPattern = (h >>> 20) % 3;

  const palette: Record<string, string | null> = {
    ".": null,
    k: "#000000",
    s: skin,
    h: hair,
    H: hat,
    B: shirt,
    b: shadeColor(shirt, -20),
    w: "#ffffff",
    g: "#c0c0c0",
  };

  const g: string[][] = Array.from({ length: 16 }, () =>
    Array<string>(16).fill("."),
  );
  const set = (x: number, y: number, c: string) => {
    if (x >= 0 && y >= 0 && x < 16 && y < 16) g[y][x] = c;
  };
  const rect = (x: number, y: number, w: number, hh: number, c: string) => {
    for (let yy = y; yy < y + hh; yy++)
      for (let xx = x; xx < x + w; xx++) set(xx, yy, c);
  };

  // head outline
  rect(4, 2, 8, 1, "k");
  rect(3, 3, 1, 6, "k");
  rect(12, 3, 1, 6, "k");
  rect(4, 9, 8, 1, "k");
  rect(4, 3, 8, 6, "s");

  // hair
  if (hairStyle !== 2) {
    if (hairStyle === 0) {
      rect(4, 3, 8, 1, "h");
      rect(4, 4, 1, 1, "h");
      rect(11, 4, 1, 1, "h");
    } else {
      rect(4, 3, 8, 2, "h");
      rect(3, 4, 1, 5, "h");
      rect(12, 4, 1, 5, "h");
    }
  } else {
    rect(5, 3, 6, 1, "s");
  }

  // hat
  if (hasHat) {
    rect(3, 1, 10, 1, "k");
    rect(2, 2, 12, 1, "k");
    rect(3, 2, 10, 1, "H");
    rect(2, 3, 12, 1, "H");
    rect(2, 3, 1, 1, "k");
    rect(13, 3, 1, 1, "k");
  }

  // eyes
  set(6, 6, "k");
  set(9, 6, "k");
  if (hasGlasses) {
    rect(5, 5, 3, 3, "k");
    rect(8, 5, 3, 3, "k");
    rect(6, 6, 1, 1, "w");
    rect(9, 6, 1, 1, "w");
  }

  // mouth
  if (hasMustache) {
    rect(6, 7, 4, 1, "h");
    set(7, 8, "k");
    set(8, 8, "k");
  } else {
    set(7, 8, "k");
    set(8, 8, "k");
  }

  // neck
  rect(7, 10, 2, 1, "s");

  // body
  rect(3, 11, 10, 1, "k");
  rect(2, 12, 1, 4, "k");
  rect(13, 12, 1, 4, "k");
  rect(3, 12, 10, 4, "B");

  // pattern
  if (shirtPattern === 1) {
    for (let x = 3; x < 13; x += 2) rect(x, 12, 1, 4, "b");
  } else if (shirtPattern === 2) {
    rect(6, 11, 4, 1, "w");
    set(7, 12, "w");
    set(8, 12, "w");
  }

  // bottom outline
  rect(2, 15, 12, 1, "k");

  return { palette, map: g.map((row) => row.join("")) };
}
