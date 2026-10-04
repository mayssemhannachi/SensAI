// components/ui/Sticker.tsx
import Image from "next/image";

export default function Sticker({
  name,
  size = 56,
  className = "",
}: {
  name: string;
  size?: number;
  className?: string;
}) {
  return (
    <div
      className={`pointer-events-none absolute ${className}`}
      style={{ width: size, height: size }}
    >
      <Image
        src={`/Assets/Landing Page/stickers/${name}.png`}
        alt=""
        width={size}
        height={size}
        className="h-full w-full object-contain"
      />
    </div>
  );
}
