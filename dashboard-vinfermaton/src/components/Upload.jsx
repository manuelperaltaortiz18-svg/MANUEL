import { useRef, useState } from 'react';
import { parseBusinessReport } from '../lib/csv.js';
import { COLORS } from '../theme.js';

/** Intenta sacar la fecha de corte del nombre del fichero: BusinessReport-01-09-26.csv */
function fechaDesdeNombre(name) {
  const m = name.match(/(\d{2})-(\d{2})-(\d{2})(?!\d)/);
  if (!m) return null;
  const [, dd, mm, yy] = m;
  return `20${yy}-${mm}-${dd}`;
}

export function Upload({ onSnapshot }) {
  const inputRef = useRef(null);
  const [drag, setDrag] = useState(false);
  const [msg, setMsg] = useState(null);

  async function handleFiles(files) {
    const file = files?.[0];
    if (!file) return;
    const text = await file.text();
    const { rows, warnings, delimiter } = parseBusinessReport(text);

    if (rows.length === 0) {
      setMsg({ tipo: 'error', texto: 'No se pudo leer ninguna fila. ¿Es un Business Report de Amazon?' });
      return;
    }

    const fecha = fechaDesdeNombre(file.name) || new Date().toISOString().slice(0, 10);
    onSnapshot({ fecha, origen: file.name, rows });
    setMsg({
      tipo: warnings.length ? 'aviso' : 'ok',
      texto: `${rows.length} ASINs cargados (corte ${fecha}, delimitador "${delimiter}").`,
      warnings,
    });
  }

  const color = msg?.tipo === 'error' ? COLORS.red : msg?.tipo === 'aviso' ? COLORS.orange : COLORS.green;

  return (
    <div className="card">
      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); handleFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        style={{
          border: `2px dashed ${drag ? COLORS.blue : COLORS.border}`,
          borderRadius: 8, padding: '22px 16px', textAlign: 'center', cursor: 'pointer',
          background: drag ? '#1e3a52' : 'transparent',
        }}
      >
        <div style={{ fontWeight: 600 }}>Arrastra aquí el Business Report CSV</div>
        <div style={{ color: COLORS.muted, fontSize: 12, marginTop: 4 }}>
          o haz clic para seleccionarlo. La fecha se toma del nombre (BusinessReport-01-09-26.csv).
        </div>
        <input
          ref={inputRef} type="file" accept=".csv,text/csv" hidden
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>
      {msg && (
        <div style={{ marginTop: 10, color, fontSize: 13 }}>
          {msg.texto}
          {msg.warnings?.map((w) => (
            <div key={w} style={{ color: COLORS.orange, fontSize: 12, marginTop: 2 }}>⚠ {w}</div>
          ))}
        </div>
      )}
    </div>
  );
}
