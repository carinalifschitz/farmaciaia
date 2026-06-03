import axios from 'axios';

export const subirEInterpretarImagen = async (file) => {
  if (!file) return;

  // Creamos el formulario virtual multipart/form-data
  const formData = new FormData();
  formData.append('imagen', file); // 'imagen' coincide con request.files['imagen'] en Flask

  try {
    const response = await axios.post('[http://127.0.0.1:5000/api/interpretar-imagen](http://127.0.0.1:5000/api/interpretar-imagen)', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    // Recibes directamente el arreglo parsed: [{ producto: "Ibuprofeno 400mg", cantidad: 3 }]
    return response.data; 
  } catch (error) {
    console.error("Error enviando imagen al backend:", error);
    throw new Error(error.response?.data?.error || "Error al conectar con el servidor.");
  }
};