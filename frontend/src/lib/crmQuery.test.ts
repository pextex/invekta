import { describe, it, expect, vi, afterEach } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import { crmRequest } from "./crmQuery";
import { ApiError } from "./api";

afterEach(() => vi.unstubAllGlobals());
function response(status = 200) {
  vi.stubGlobal("window", { location: { protocol: "http:" } });
  vi.stubGlobal(
    "fetch",
    async () =>
      new Response(
        JSON.stringify(
          status === 200 ? { version: 2 } : { detail: "Conflict" },
        ),
        { status, headers: { "content-type": "application/json" } },
      ),
  );
}
describe("shared CRM state", () => {
  it("invalidates all related unit views only after a successful persisted mutation", async () => {
    const client = new QueryClient();
    const keys = [
      "/summary",
      "/opportunities",
      "/companies/1",
      "/companies/1/contacts",
    ];
    keys.forEach((path) =>
      client.setQueryData(["crm", 1, path], { old: true }),
    );
    client.setQueryData(["crm", 2, "/summary"], { private: true });
    response();
    expect(
      await crmRequest(client, 1, "/opportunities/1/stage", {
        method: "PATCH",
        body: "{}",
      }),
    ).toEqual({ version: 2 });
    keys.forEach((path) =>
      expect(client.getQueryState(["crm", 1, path])?.isInvalidated).toBe(true),
    );
    expect(client.getQueryState(["crm", 2, "/summary"])?.isInvalidated).toBe(
      false,
    );
    client.clear();
  });
  it("refreshes stale views on 409 without claiming that the write succeeded", async () => {
    const client = new QueryClient();
    client.setQueryData(["crm", 1, "/summary"], { won_count: 0 });
    response(409);
    await expect(
      crmRequest(client, 1, "/opportunities/1/stage", { method: "PATCH" }),
    ).rejects.toBeInstanceOf(ApiError);
    expect(client.getQueryState(["crm", 1, "/summary"])?.isInvalidated).toBe(
      true,
    );
    expect(client.getQueryData(["crm", 1, "/summary"])).toEqual({
      won_count: 0,
    });
    client.clear();
  });
  it("does not mark rejected unauthorized writes as persisted", async () => {
    const client = new QueryClient();
    client.setQueryData(["crm", 1, "/summary"], { won_count: 0 });
    response(403);
    await expect(
      crmRequest(client, 1, "/opportunities/1/stage", { method: "PATCH" }),
    ).rejects.toBeInstanceOf(ApiError);
    expect(client.getQueryState(["crm", 1, "/summary"])?.isInvalidated).toBe(
      false,
    );
    client.clear();
  });
});
