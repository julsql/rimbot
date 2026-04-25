import { useEffect, useState } from "react";
import { fetchSyllables } from "../api/client.js";

export default function HelpPage() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    fetchSyllables()
      .then((data) => alive && setRows(data))
      .catch((err) => alive && setError(err.message || "Erreur réseau"));
    return () => {
      alive = false;
    };
  }, []);

  return (
    <article className="help">
      <h1>Aide phonétique</h1>
      <p>
        Liste des syllabes utilisables pour imposer des rimes (présentes au
        moins 10 fois dans la base).
      </p>

      {error && <p className="error">{error}</p>}
      {!rows && !error && <p>Chargement…</p>}

      {rows && (
        <table className="phon-table">
          <thead>
            <tr>
              <th>Syllabes</th>
              <th>Courant</th>
              <th>API</th>
              <th>Occurrences</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.API}>
                <td>{r.courant}</td>
                <td>{r.dersyll}</td>
                <td>{r.API}</td>
                <td>{r.nboccurence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </article>
  );
}
