import PixelSprite from "./PixelSprite";
import { CHARACTERS, type CharacterId } from "./characters";
import { generateAvatar } from "./generate";

interface AvatarProps {
  seed?: string;
  characterId?: CharacterId | string | null;
  scale?: number;
  className?: string;
}

export default function Avatar({
  seed,
  characterId,
  scale = 4,
  className,
}: AvatarProps) {
  const fixed =
    characterId && characterId in CHARACTERS
      ? CHARACTERS[characterId as CharacterId]
      : null;
  const def = fixed ?? generateAvatar(seed ?? "anon");

  return (
    <PixelSprite
      map={def.map}
      palette={def.palette}
      scale={scale}
      className={className}
    />
  );
}
