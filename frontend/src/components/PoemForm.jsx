import { useState } from "react";

const PRESETS = {
  "Sonnet":  { forme: "ABBA CDDC EEF GGF", sylla: "1=12", phone: "" },
  "Haïku":   { forme: "ABA",                sylla: "1=5,2=7,3=5", phone: "" },
  "Ballade": { forme: "ABABBCBC ABABBCBC ABABBCBC BCBC", sylla: "1=10", phone: "" },
};

export default function PoemForm({ onSubmit, isLoading }) {
  const [form, setForm] = useState({ forme: "", sylla: "", phone: "" });

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  const applyPreset = (name) => () => setForm({ ...PRESETS[name] });

  const submit = (e) => {
    e.preventDefault();
    onSubmit?.(form);
  };

  return (
    <form className="poem-form" onSubmit={submit} aria-label="Formulaire de génération">
      <div className="presets">
        {Object.keys(PRESETS).map((name) => (
          <button type="button" key={name} className="button" onClick={applyPreset(name)}>
            {name}
          </button>
        ))}
      </div>

      <label>
        Forme (ABBA, ABAB …)
        <input
          type="text"
          required
          placeholder="Forme du poème"
          value={form.forme}
          onChange={update("forme")}
        />
      </label>

      <label>
        Syllabes (1=12, 4=8 …)
        <input
          type="text"
          placeholder="Nombre de syllabes par vers"
          value={form.sylla}
          onChange={update("sylla")}
        />
      </label>

      <label>
        Phonétique des rimes (A=t@t, B=se …)
        <input
          type="text"
          placeholder="Rimes imposées"
          value={form.phone}
          onChange={update("phone")}
        />
      </label>

      <button type="submit" className="button primary" disabled={isLoading}>
        {isLoading ? "Génération en cours…" : "Générer"}
      </button>
    </form>
  );
}
