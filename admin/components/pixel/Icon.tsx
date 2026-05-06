import PixelSprite from "./PixelSprite";
import { ICONS, type IconName } from "./icons";

interface IconProps {
  name: IconName;
  scale?: number;
  className?: string;
}

export default function Icon({ name, scale = 1, className }: IconProps) {
  const def = ICONS[name];
  return (
    <PixelSprite
      map={def.map}
      palette={def.palette}
      scale={scale}
      className={className}
    />
  );
}
