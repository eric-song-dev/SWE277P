import { useCallback, useMemo, useRef, useState, type ReactNode } from "react";
import type { CommitSummary, ImportPreview } from "../../api/types";
import { UploadContext, type EventFormValues, type UploadCard } from "./uploadStore";

// The Upload page's cards and the edits typed into them live above the routes (the app shell
// owns this provider), so leaving /upload and coming back keeps them. Memory only: a full
// reload starts again from the server's pending imports and their prefilled drafts.

export function UploadProvider({ children }: { children: ReactNode }) {
  const [cards, setCards] = useState<UploadCard[]>([]);
  const [forms, setForms] = useState<Record<number, EventFormValues>>({});
  const nextKey = useRef(0);

  const addPreviews = useCallback((previews: ImportPreview[]) => {
    setCards((current) => {
      // Re-dropping a pending file returns the same import, which already has a card, and one
      // batch can hold the same import twice (two copies of one export).
      const seen = new Set(current.map((c) => c.preview.id).filter((id) => id !== null));
      const added: UploadCard[] = [];
      for (const preview of previews) {
        if (preview.id !== null) {
          if (seen.has(preview.id)) continue;
          seen.add(preview.id);
        }
        added.push({
          key: preview.id === null ? `file-${nextKey.current++}` : `import-${preview.id}`,
          preview,
          summary: null,
        });
      }
      return added.length === 0 ? current : [...added, ...current];
    });
  }, []);

  const removeCard = useCallback((key: string) => {
    setCards((current) => current.filter((c) => c.key !== key));
  }, []);

  const setSummary = useCallback((key: string, summary: CommitSummary) => {
    setCards((current) => current.map((c) => (c.key === key ? { ...c, summary } : c)));
  }, []);

  const setFormValues = useCallback((importId: number, values: EventFormValues) => {
    setForms((current) => ({ ...current, [importId]: values }));
  }, []);

  const formValues = useCallback((importId: number) => forms[importId], [forms]);

  const store = useMemo(
    () => ({ cards, addPreviews, removeCard, setSummary, formValues, setFormValues }),
    [cards, addPreviews, removeCard, setSummary, formValues, setFormValues],
  );
  return <UploadContext.Provider value={store}>{children}</UploadContext.Provider>;
}
