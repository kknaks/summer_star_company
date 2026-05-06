import Icon from "@/components/pixel/Icon";
import type { IconName } from "@/components/pixel/icons";

interface TitleBarProps {
  title: string;
  icon?: IconName;
  onMin?: () => void;
  onMax?: () => void;
  onClose?: () => void;
  inactive?: boolean;
}

export default function TitleBar({
  title,
  icon = "computer",
  onMin,
  onMax,
  onClose,
  inactive,
}: TitleBarProps) {
  return (
    <div className={`title-bar ${inactive ? "inactive" : ""}`}>
      <div className="title-bar-icon">
        <Icon name={icon} scale={1} />
      </div>
      <div className="title-bar-text">{title}</div>
      <div className="title-bar-controls">
        <button
          type="button"
          className="tb-btn"
          onClick={onMin}
          aria-label="최소화"
        >
          _
        </button>
        <button
          type="button"
          className="tb-btn"
          onClick={onMax}
          aria-label="최대화"
        >
          ▢
        </button>
        <button
          type="button"
          className="tb-btn"
          onClick={onClose}
          aria-label="닫기"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
