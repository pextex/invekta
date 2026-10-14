import { useState } from "react";
import WorkBoard from "./WorkBoard";
import ReminderInbox from "./ReminderInbox";
import type { Company } from "./types";
export default function WorkSpace({
  unit,
  companies,
  companyId,
}: {
  unit: number;
  companies: Company[];
  companyId?: number;
}) {
  const [tab, setTab] = useState("tasks");
  return (
    <div className="reports-panels">
      <div className="profile-tabs" aria-label="Prikaz obaveza">
        <button
          className={tab === "tasks" ? "active" : ""}
          onClick={() => setTab("tasks")}
        >
          Zadaci
        </button>
        <button
          className={tab === "activities" ? "active" : ""}
          onClick={() => setTab("activities")}
        >
          Aktivnosti
        </button>
        <button
          className={tab === "reminders" ? "active" : ""}
          onClick={() => setTab("reminders")}
        >
          Podsetnici
        </button>
      </div>
      {tab === "reminders" ? (
        <ReminderInbox unit={unit} companyId={companyId} />
      ) : (
        <WorkBoard
          key={`${tab}-${companyId ?? "all"}`}
          unit={unit}
          kind={tab === "tasks" ? "tasks" : "activities"}
          companies={companies}
          companyId={companyId}
        />
      )}
    </div>
  );
}
