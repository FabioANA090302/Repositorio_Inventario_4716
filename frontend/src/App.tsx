import { useEffect, useState } from "react";

function App() {
  const [labs, setLabs] = useState<string[]>([]);
  const [selectedLab, setSelectedLab] = useState<string>("");

  const [data, setData] = useState<any[]>([]);
  const [search, setSearch] = useState("");

  const [page, setPage] = useState(1);
  const PAGE_SIZE = 30;

  // Estados para selección y pedido
  const [selectedItems, setSelectedItems] = useState<any[]>([]);
  const [showResumen, setShowResumen] = useState(false);
  const [cantidades, setCantidades] = useState<{ [key: string]: number }>({});
  const [ultimoTicket, setUltimoTicket] = useState<number | null>(null);

  // 🔹 obtener lista de laboratorios
  useEffect(() => {
    fetch("/laboratorios") // <- Ruta relativa
      .then(res => res.json())
      .then(res => setLabs(res.laboratorios));
  }, []);

  // 🔹 cargar un laboratorio al seleccionar
  useEffect(() => {
    if (!selectedLab) return;

    fetch(`/laboratorio?nombre=${encodeURIComponent(selectedLab)}`) // <- Ruta relativa
      .then(res => res.json())
      .then(res => {
        const filasConId = res.filas.map((fila: any, index: number) => ({ ...fila, id: index }));
        setData(filasConId);
        setPage(1);
        setSelectedItems([]);
        setCantidades({});
      });
  }, [selectedLab]);

  // 🔍 búsqueda global
  const filtered = data.filter(item =>
    JSON.stringify(item).toLowerCase().includes(search.toLowerCase())
  );

  // 📌 paginación visual
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // 🔹 Toggle de selección
  const toggleSelect = (item: any) => {
    const alreadySelected = selectedItems.find(i => i.id === item.id);
    if (alreadySelected) {
      setSelectedItems(selectedItems.filter(i => i.id !== item.id));
      const newCant = { ...cantidades };
      delete newCant[item.id];
      setCantidades(newCant);
    } else {
      setSelectedItems([...selectedItems, item]);
      setCantidades({ ...cantidades, [item.id]: 1 });
    }
  };

  // 🔹 Manejar cambio de cantidad en resumen
  const handleCantidadChange = (item: any, value: number) => {
    const disponible = item["CANT"] || 1;
    if (value > disponible) {
      alert(`No hay suficiente existencia. Disponible: ${disponible}`);
      value = disponible;
    }
    setCantidades({ ...cantidades, [item.id]: value });
  };

  // 🔹 Confirmar pedido: enviar al backend
  const confirmarPedido = () => {
    const payload = {
      laboratorio: selectedLab,
      items: selectedItems.map(item => ({
        id: item.id,
        DESCRIPCIÓN: item["DESCRIPCIÓN"],
        CANT: cantidades[item.id],
        UBICACIÓN: item["UBICACIÓN"]
      }))
    };

    fetch("/pedir", { // <- Ruta relativa
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(res => {
        if (res.ok) {
          setUltimoTicket(res.ticket_id);
          alert(`Pedido enviado! Ticket #${res.ticket_id}`);
          setSelectedItems([]);
          setCantidades({});
          setShowResumen(false);
        } else {
          alert(`Error al enviar pedido: ${res.error}`);
        }
      });
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Sistema de Pedidos</h1>

      {/* Mostrar ticket último pedido si existe */}
      {ultimoTicket && (
        <div style={{ padding: 10, marginBottom: 20, backgroundColor: "#d4edda", color: "#155724" }}>
          ✅ Pedido enviado correctamente. Tu Ticket es: <strong>{ultimoTicket}</strong>
        </div>
      )}

      {/* 🔹 Buscador */}
      <input
        placeholder="Buscar..."
        value={search}
        onChange={e => {
          setSearch(e.target.value);
          setPage(1);
        }}
        style={{ padding: 10, width: "50%", marginBottom: 20 }}
      />

      {/* 🔹 Pestañas por laboratorio */}
      <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
        {labs.map(lab => (
          <button
            key={lab}
            onClick={() => setSelectedLab(lab)}
            style={{
              padding: 10,
              background: selectedLab === lab ? "#4CAF50" : "#ddd",
              border: "none",
              cursor: "pointer"
            }}
          >
            {lab}
          </button>
        ))}
      </div>

      {/* 🔹 Tabla filtrada */}
      <table border={1} cellPadding={8}>
        <thead>
          <tr>
            <th>Sel.</th>
            <th>CANT</th>
            <th>DESCRIPCIÓN</th>
            <th>MODELO</th>
            <th>ESTADO</th>
            <th>V/R UNIT</th>
          </tr>
        </thead>
        <tbody>
          {paginated.map((item, i) => (
            <tr key={i}>
              <td>
                <input
                  type="checkbox"
                  checked={!!selectedItems.find(it => it.id === item.id)}
                  onChange={() => toggleSelect(item)}
                />
              </td>
              <td>{item["CANT"]}</td>
              <td>{item["DESCRIPCIÓN"]}</td>
              <td>{item["MODELO"]}</td>
              <td>{item["ESTADO"]}</td>
              <td>{item["V/R UNIT"]}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 🔹 Paginación */}
      <div style={{ marginTop: 20 }}>
        <button disabled={page === 1} onClick={() => setPage(page - 1)}>⬅ Anterior</button>
        <span style={{ margin: "0 10px" }}>Página {page} de {totalPages}</span>
        <button disabled={page === totalPages} onClick={() => setPage(page + 1)}>Siguiente ➡</button>
      </div>

      {/* 🔹 Botón pedir */}
      <button
        onClick={() => setShowResumen(true)}
        disabled={selectedItems.length === 0}
        style={{ marginTop: 20, padding: 10 }}
      >
        Pedir
      </button>

      {/* 🔹 Resumen del pedido */}
      {showResumen && (
        <div style={{ border: "1px solid #333", padding: 20, marginTop: 20 }}>
          <h2>Resumen de Pedido</h2>
          {selectedItems.map((item, idx) => (
            <div key={idx} style={{ marginBottom: 10 }}>
              <strong>{item["DESCRIPCIÓN"]}</strong> - Disponible: {item["CANT"] || 1}
              <br />
              <input
                type="number"
                min={1}
                value={cantidades[item.id]}
                onChange={e => handleCantidadChange(item, parseInt(e.target.value))}
              />
            </div>
          ))}
          <button onClick={confirmarPedido} style={{ marginTop: 10 }}>Confirmar Pedido</button>
          <button onClick={() => setShowResumen(false)} style={{ marginTop: 10, marginLeft: 10 }}>Cancelar</button>
        </div>
      )}
    </div>
  );
}

export default App;
