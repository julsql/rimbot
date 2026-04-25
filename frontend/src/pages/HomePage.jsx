import { useState } from "react";
import PoemForm from "../components/PoemForm.jsx";
import PoemDisplay from "../components/PoemDisplay.jsx";
import { generatePoem } from "../api/client.js";

export default function HomePage() {
  const [poem, setPoem] = useState(null);
  const [errors, setErrors] = useState({ err1: "", err2: "" });
  const [isLoading, setLoading] = useState(false);

  const onSubmit = async (data) => {
    setLoading(true);
    setPoem(null);
    setErrors({ err1: "", err2: "" });
    try {
      const resp = await generatePoem(data);
      setPoem(resp.poem || null);
      setErrors({ err1: resp.err1 || "", err2: resp.err2 || "" });
    } catch (err) {
      const body = err?.response?.data;
      setErrors({
        err1: body?.err1 || "Erreur lors de la génération",
        err2: body?.err2 || "",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <article>
      <section className="spotlight">
        <div className="content-col">
          <h1>Générateur</h1>
          <p>
            Choisissez la forme de votre poème (par ex. <code>ABBA</code>),
            le nombre de syllabes par vers et éventuellement les rimes
            imposées. Consultez l'<a href="/aide">aide phonétique</a> pour les
            syllabes disponibles.
          </p>
          <PoemForm onSubmit={onSubmit} isLoading={isLoading} />
          {errors.err1 && <p className="error">{errors.err1}</p>}
          {errors.err2 && <p className="error">{errors.err2}</p>}
        </div>
        <span className="image">
          <img src="/plume.png" alt="Plume" />
        </span>
      </section>

      <PoemDisplay poem={poem} />
    </article>
  );
}
