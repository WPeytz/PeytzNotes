import type { NoteSummary } from "@/lib/api";

export interface NoteFolder {
  name: string;
  path: string;
  folders: Map<string, NoteFolder>;
  notes: NoteSummary[];
  overview: NoteSummary | null;
  count: number;
}

const notionId = /\s+[a-f0-9]{20,}$/i;

function cleanName(name: string): string {
  return name.replace(notionId, "");
}

function createFolder(name: string, path: string): NoteFolder {
  return { name, path, folders: new Map(), notes: [], overview: null, count: 0 };
}

function finishFolder(folder: NoteFolder): void {
  folder.notes = folder.notes.filter((note) => {
    const filename = note.source_path.split("/").at(-1)?.replace(/\.md$/i, "") || "";
    const child = folder.folders.get(cleanName(filename));
    if (child && !child.overview) {
      child.overview = note;
      return false;
    }
    return true;
  });

  folder.count = folder.notes.length + Number(Boolean(folder.overview));
  for (const child of folder.folders.values()) {
    finishFolder(child);
    folder.count += child.count;
  }
}

export function buildNotesTree(notes: NoteSummary[]): NoteFolder {
  const root = createFolder("", "");
  for (const note of notes) {
    const parts = note.source_path.split("/").filter(Boolean);
    let folder = root;
    for (const rawPart of parts.slice(0, -1)) {
      const name = rawPart === "uploads" ? "Uploaded notes" : cleanName(rawPart);
      if (!folder.folders.has(name)) {
        folder.folders.set(name, createFolder(name, `${folder.path}/${name}`));
      }
      folder = folder.folders.get(name)!;
    }
    folder.notes.push(note);
  }
  finishFolder(root);
  return root;
}

export function filterNotesTree(
  folder: NoteFolder,
  query: string,
  ancestorMatches = false,
): NoteFolder | null {
  const term = query.trim().toLocaleLowerCase();
  if (!term) return folder;

  const matches = ancestorMatches || folder.name.toLocaleLowerCase().includes(term);
  const overview = folder.overview && (
    matches || folder.overview.title.toLocaleLowerCase().includes(term)
  ) ? folder.overview : null;
  const notes = folder.notes.filter((note) =>
    matches || note.title.toLocaleLowerCase().includes(term)
  );
  const children = new Map<string, NoteFolder>();
  let count = notes.length + Number(Boolean(overview));
  for (const [name, child] of folder.folders) {
    const filtered = filterNotesTree(child, term, matches);
    if (filtered) {
      children.set(name, filtered);
      count += filtered.count;
    }
  }
  return count ? { ...folder, folders: children, notes, overview, count } : null;
}

export const noteNameSort = new Intl.Collator(undefined, {
  numeric: true,
  sensitivity: "base",
});
