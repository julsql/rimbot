import { describe, it, expect, vi, beforeEach } from "vitest";
import { api, generatePoem, previewPoem, fetchSyllables } from "../api/client.js";

describe("api client", () => {
  beforeEach(() => {
    vi.spyOn(api, "post").mockReset();
    vi.spyOn(api, "get").mockReset();
  });

  it("generatePoem POST /poem/generate avec le body fourni", async () => {
    const post = vi.spyOn(api, "post").mockResolvedValue({
      data: { poem: ["x"], err1: "", err2: "" },
    });
    const out = await generatePoem({ forme: "ABBA", sylla: "1=12", phone: "" });
    expect(post).toHaveBeenCalledWith("/poem/generate", {
      forme: "ABBA",
      sylla: "1=12",
      phone: "",
    });
    expect(out.poem).toEqual(["x"]);
  });

  it("previewPoem POST /poem/preview", async () => {
    const post = vi.spyOn(api, "post").mockResolvedValue({
      data: { preview: "_ A", err1: "", err2: "" },
    });
    const out = await previewPoem({ forme: "A", sylla: "", phone: "" });
    expect(post).toHaveBeenCalledWith("/poem/preview", {
      forme: "A",
      sylla: "",
      phone: "",
    });
    expect(out.preview).toBe("_ A");
  });

  it("fetchSyllables GET /help/syllables", async () => {
    const get = vi.spyOn(api, "get").mockResolvedValue({
      data: [{ courant: "t@t", dersyll: "tat", API: "t@t", nboccurence: 42 }],
    });
    const data = await fetchSyllables();
    expect(get).toHaveBeenCalledWith("/help/syllables");
    expect(data).toHaveLength(1);
  });
});
