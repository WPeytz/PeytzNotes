import Link from "next/link";
import { Source } from "@/lib/api";

export default function SourceLink({ source, className }: { source: Source; className?: string }) {
  const section = source.heading ? `?section=${encodeURIComponent(source.heading)}` : "";
  return (
    <Link href={`/notes/${source.note_id}${section}`} className={className || "text-blue-400 hover:underline"}>
      {source.note_title}{source.heading ? ` · ${source.heading}` : ""}
    </Link>
  );
}
