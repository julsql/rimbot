export default function PoemDisplay({ poem }) {
  if (!poem || poem.length === 0) {
    return null;
  }

  const download = () => {
    const blob = new Blob([poem.join("\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "poeme.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="poem-display" aria-label="Poème généré">
      <pre className="poem">
        {poem.map((line, i) => (
          <span key={i}>
            {line}
            {"\n"}
          </span>
        ))}
      </pre>
      <button type="button" className="button" onClick={download}>
        Télécharger
      </button>
    </section>
  );
}
