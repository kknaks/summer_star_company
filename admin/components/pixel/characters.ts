import type { CharacterId } from "@/lib/types";

import type { SpriteDef } from "./icons";

export type { CharacterId };

export interface CharacterMeta {
  id: CharacterId;
  label: string;
  gender: "F" | "M";
}

type HairStyle = "short" | "long" | "bun" | "spiky";

interface CharOpts {
  skin: string;
  hair: string;
  hairStyle: HairStyle;
  shirt: string;
  accent: string;
  hat?: string;
  glasses?: boolean;
  mustache?: boolean;
  lips?: string;
}

function makeChar(opts: CharOpts): SpriteDef {
  const {
    skin,
    hair,
    hairStyle,
    shirt,
    accent,
    hat,
    glasses,
    mustache,
    lips,
  } = opts;

  const palette: Record<string, string | null> = {
    ".": null,
    k: "#000000",
    s: skin,
    h: hair,
    B: shirt,
    b: accent,
    H: hat ?? "#c81e1e",
    w: "#ffffff",
    l: lips ?? "#c81e1e",
  };

  const g: string[][] = Array.from({ length: 16 }, () =>
    Array<string>(16).fill("."),
  );
  const set = (x: number, y: number, c: string) => {
    if (x >= 0 && y >= 0 && x < 16 && y < 16) g[y][x] = c;
  };
  const rect = (x: number, y: number, w: number, h: number, c: string) => {
    for (let yy = y; yy < y + h; yy++)
      for (let xx = x; xx < x + w; xx++) set(xx, yy, c);
  };

  // head outline
  rect(4, 2, 8, 1, "k");
  rect(3, 3, 1, 6, "k");
  rect(12, 3, 1, 6, "k");
  rect(4, 9, 8, 1, "k");
  rect(4, 3, 8, 6, "s");

  // hair
  if (hairStyle === "short") {
    rect(4, 3, 8, 1, "h");
    set(4, 4, "h");
    set(11, 4, "h");
  } else if (hairStyle === "long") {
    rect(4, 3, 8, 2, "h");
    rect(3, 4, 1, 5, "h");
    rect(12, 4, 1, 5, "h");
    rect(2, 9, 2, 2, "h");
    rect(12, 9, 2, 2, "h");
  } else if (hairStyle === "bun") {
    rect(4, 3, 8, 2, "h");
    rect(3, 4, 1, 4, "h");
    rect(12, 4, 1, 4, "h");
    rect(6, 1, 4, 2, "h");
    set(5, 2, "h");
    set(10, 2, "h");
  } else if (hairStyle === "spiky") {
    rect(4, 3, 8, 1, "h");
    set(5, 2, "h");
    set(7, 2, "h");
    set(9, 2, "h");
    set(11, 2, "h");
    set(4, 4, "h");
    set(11, 4, "h");
  }

  // hat
  if (hat) {
    rect(3, 1, 10, 1, "k");
    rect(2, 2, 12, 1, "k");
    rect(3, 2, 10, 1, "H");
    rect(2, 3, 12, 1, "H");
    set(2, 3, "k");
    set(13, 3, "k");
  }

  // eyes
  set(6, 6, "k");
  set(9, 6, "k");
  if (glasses) {
    rect(5, 5, 3, 3, "k");
    rect(8, 5, 3, 3, "k");
    set(6, 6, "w");
    set(9, 6, "w");
  }

  // mouth
  if (mustache) {
    rect(6, 7, 4, 1, "h");
    set(7, 8, "k");
    set(8, 8, "k");
  } else if (lips) {
    set(7, 8, "l");
    set(8, 8, "l");
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
  rect(2, 15, 12, 1, "k");

  // collar accent
  rect(6, 11, 4, 1, "b");
  set(7, 12, "b");
  set(8, 12, "b");

  return { palette, map: g.map((r) => r.join("")) };
}

export const CHARACTERS: Record<CharacterId, SpriteDef> = {
  c_f1: makeChar({
    skin: "#fcd0a0",
    hair: "#3a2410",
    hairStyle: "long",
    shirt: "#c81e1e",
    accent: "#a01010",
    lips: "#e04040",
  }),
  c_f2: makeChar({
    skin: "#fcb98e",
    hair: "#5a3a1a",
    hairStyle: "bun",
    shirt: "#1a8060",
    accent: "#0e5040",
    lips: "#d04040",
  }),
  c_m1: makeChar({
    skin: "#f1a675",
    hair: "#1a1a1a",
    hairStyle: "short",
    shirt: "#000080",
    accent: "#0040a0",
    glasses: true,
  }),
  c_m2: makeChar({
    skin: "#d39060",
    hair: "#3a2410",
    hairStyle: "spiky",
    shirt: "#806020",
    accent: "#503010",
    mustache: true,
  }),
};

export const CHARACTER_LIST: CharacterMeta[] = [
  { id: "c_f1", label: "여 · 긴머리", gender: "F" },
  { id: "c_f2", label: "여 · 묶음머리", gender: "F" },
  { id: "c_m1", label: "남 · 안경", gender: "M" },
  { id: "c_m2", label: "남 · 콧수염", gender: "M" },
];
