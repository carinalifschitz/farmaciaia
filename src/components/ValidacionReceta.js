import { useState, useRef } from "react";
import { ShieldCheck, FileText, PackageCheck, Loader2 } from "lucide-react"; 

export default function ValidacionReceta() {
  const [receta, setReceta] = useState("");
  const [medicamentos, setMedicamentos] = useState("");
  const [resultado, setResultado] = useState(""); 
  const [cargando, setCargando] = useState(false); 

  const recetaInputRef = useRef(null);
  const medicamentosInputRef = useRef(null);

  const handleRecetaUpload = (event) => {
    const file = event.target.files[0];
    if (file) setReceta(`Archivo cargado: ${file.name}\n[Simulación OCR: Paracetamol 500mg, 20 comprimidos]`);
  };

  const handleMedicamentosUpload = (event) => {
    const file = event.target.files[0];
    if (file) setMedicamentos(`Archivo cargado: ${file.name}\n[Simulación Vision: Paracetamol 500mg, 10 comprimidos]`);
  };

  const manejarValidacionConIA = async () => {
    if (!receta || !medicamentos) {
      alert("Por favor, completa ambos campos antes de validar.");
      return;
    }

    setCargando(true);
    setResultado("");

    try {
      const respuesta = await fetch("http://127.0.0.1:5000/api/validar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          receta: receta,
          remedios: medicamentos,
        }),
      });

      const datos = await respuesta.json();
      if (datos.resultado) {
        setResultado(datos.resultado);
      } else {
        setResultado("❌ Ocurrió un error inesperado al recibir la respuesta.");
      }
    } catch (error) {
      setResultado(`❌ No se pudo conectar con el servidor backend: ${error.message}`);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 p-4">
      <div className="max-w-md mx-auto space-y-6">

        {/* Título Principal */}
        <div className="bg-gradient-to-r from-blue-700 to-emerald-600 rounded-3xl p-6 shadow-lg text-white">
          <div className="flex items-center gap-3 mb-2">
            <ShieldCheck size={34} />
            <h1 className="text-2xl font-bold">Validación de Entrega</h1>
          </div>
          <p className="text-sm text-blue-100">
            Comparación inteligente entre receta médica y productos entregados.
          </p>
        </div>

        {/* Receta Médica */}
        <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-200">
          <div className="flex items-center gap-2 mb-3">
            <FileText className="text-blue-600" size={22} />
            <h2 className="text-lg font-semibold text-slate-800">Receta Médica</h2>
          </div>
          <textarea
            className="w-full border border-slate-300 rounded-xl p-3 text-sm bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400"
            rows={4}
            value={receta}
            onChange={(e) => setReceta(e.target.value)}
            placeholder="Texto reconocido de la receta..."
          />
          <div className="mt-3">
            <button
              onClick={() => recetaInputRef.current.click()}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded-xl transition shadow-sm text-sm"
            >
              Subir Receta
            </button>
            <input type="file" accept="image/*" ref={recetaInputRef} onChange={handleRecetaUpload} className="hidden" />
          </div>
        </div>

        {/* Productos Entregados */}
        <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-200">
          <div className="flex items-center gap-2 mb-3">
            <PackageCheck className="text-emerald-600" size={22} />
            <h2 className="text-lg font-semibold text-slate-800">Productos Entregados</h2>
          </div>
          <textarea
            className="w-full border border-slate-300 rounded-xl p-3 text-sm bg-slate-50 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            rows={4}
            value={medicamentos}
            onChange={(e) => setMedicamentos(e.target.value)}
            placeholder="Texto reconocido de los productos..."
          />
          <div className="mt-3">
            <button
              onClick={() => medicamentosInputRef.current.click()}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-1.5 rounded-xl transition shadow-sm text-sm"
            >
              Subir Productos
            </button>
            <input type="file" accept="image/*" ref={medicamentosInputRef} onChange={handleMedicamentosUpload} className="hidden" />
          </div>
        </div>

        {/* Botón de Validación */}
        <button
          onClick={manejarValidacionConIA}
          disabled={cargando}
          className="w-full bg-slate-800 hover:bg-slate-900 text-white p-4 rounded-2xl font-semibold shadow-md transition disabled:bg-slate-400 flex justify-center items-center gap-2"
        >
          {cargando ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              Procesando con Llama 3.3...
            </>
          ) : (
            "Validar Correspondencia"
          )}
        </button>

        {/* Diagnóstico de la IA */}
        {resultado && (
          <div className="bg-white rounded-3xl p-5 shadow-md border border-slate-200">
            <h3 className="text-md font-bold text-slate-700 mb-2">Diagnóstico del Asistente IA:</h3>
            <div className="text-sm text-slate-600 whitespace-pre-line leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
              {resultado}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}