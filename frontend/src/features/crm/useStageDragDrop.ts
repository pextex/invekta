import { useRef, useState, type DragEvent } from "react";
import type { OpportunityStage } from "./types";
export function useStageDragDrop<
  T extends { id: number; stage: OpportunityStage },
>(
  items: T[],
  disabled: boolean,
  onMove: (item: T, stage: OpportunityStage) => void,
) {
  const active = useRef<number | null>(null);
  const [dragged, setDragged] = useState<number | null>(null),
    [over, setOver] = useState<OpportunityStage | null>(null);
  function finish() {
    active.current = null;
    setDragged(null);
    setOver(null);
  }
  function cardProps(item: T) {
    return {
      draggable: !disabled,
      onDragStart: (event: DragEvent<HTMLElement>) => {
        if (disabled) {
          event.preventDefault();
          return;
        }
        active.current = item.id;
        setDragged(item.id);
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData(
          "application/x-crm-opportunity",
          String(item.id),
        );
      },
      onDragEnd: finish,
    };
  }
  function columnProps(stage: OpportunityStage) {
    return {
      onDragOver: (event: DragEvent<HTMLElement>) => {
        if (disabled || active.current === null) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
        setOver(stage);
      },
      onDragLeave: (event: DragEvent<HTMLElement>) => {
        if (
          !(event.relatedTarget instanceof Node) ||
          !event.currentTarget.contains(event.relatedTarget)
        )
          setOver(null);
      },
      onDrop: (event: DragEvent<HTMLElement>) => {
        if (disabled || active.current === null) {
          finish();
          return;
        }
        event.preventDefault();
        const item = items.find((row) => row.id === active.current);
        finish();
        if (item && item.stage !== stage) onMove(item, stage);
      },
    };
  }
  return { cardProps, columnProps, dragged, over };
}
