import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "/api";

export const api = axios.create({
  baseURL,
  timeout: 60000,
});

export async function generatePoem({ forme, sylla, phone }) {
  const { data } = await api.post("/poem/generate", { forme, sylla, phone });
  return data;
}

export async function previewPoem({ forme, sylla, phone }) {
  const { data } = await api.post("/poem/preview", { forme, sylla, phone });
  return data;
}

export async function fetchSyllables() {
  const { data } = await api.get("/help/syllables");
  return data;
}
