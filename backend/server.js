const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

function construirPrompt({ modo, nombre, mail, memoria, historial }) {
    const textoBase = Array.isArray(historial)
        ? historial.map(item => `- ${item.titular || nombre || "Titular"}: ${item.texto}`).join("\n")
        : "";

    if (modo === "turak") {
        return `
Sos Turak, una voz de análisis orientada a objetivos, ejecución, dirección personal y acción concreta.

Datos del titular:
Nombre: ${nombre || "Sin nombre"}
Mail: ${mail || "Sin mail"}

Memoria contextual:
${memoria || "Sin memoria"}

Historial reciente:
${textoBase || "Sin historial"}

Tu tarea:
- dar una devolución breve pero potente
- enfocarte en objetivos, foco, obstáculos y acción
- no hacer preguntas
- hablar en tono claro, directo y útil
- responder como si le hablaras directamente al usuario
`;
    }

    return `
Sos Cirak, una voz de análisis orientada a emoción, afectividad, vínculos y mundo interno.

Datos del titular:
Nombre: ${nombre || "Sin nombre"}
Mail: ${mail || "Sin mail"}

Memoria contextual:
${memoria || "Sin memoria"}

Historial reciente:
${textoBase || "Sin historial"}

Tu tarea:
- dar una devolución breve pero profunda
- enfocarte en emoción, necesidad interna, vínculos y mundo afectivo
- no hacer preguntas
- hablar en tono cálido, humano y contenedor
- responder como si le hablaras directamente al usuario
`;
}

async function generarRespuestaReal({ provider, prompt, modo, nombre }) {
    if (provider === "demo") {
        return modo === "turak"
            ? `Turak: ${nombre || "Titular"}, tu memoria muestra material suficiente para ordenar objetivos, detectar frenos y transformar lo que venís pensando en pasos concretos de ejecución.`
            : `Cirak: ${nombre || "Titular"}, tu memoria muestra una carga emocional que merece ser escuchada con más profundidad. Hay mundo interno, afectividad y necesidad de comprensión en lo que venís registrando.`;
    }

    throw new Error("Proveedor de IA no configurado todavía.");
}

app.post("/api/analisis", async (req, res) => {
    try {
        const { modo, nombre, mail, memoria, historial } = req.body;

        if (!modo || (modo !== "turak" && modo !== "cirak")) {
            return res.status(400).json({ error: "Modo inválido." });
        }

        const prompt = construirPrompt({ modo, nombre, mail, memoria, historial });

        const resultado = await generarRespuestaReal({
            provider: process.env.AI_PROVIDER || "demo",
            prompt,
            modo,
            nombre
        });

        return res.json({
            ok: true,
            resultado
        });
    } catch (error) {
        return res.status(500).json({
            ok: false,
            error: "Error interno en análisis.",
            detalle: String(error)
        });
    }
});

app.listen(PORT, () => {
    console.log(`Servidor VISTOP escuchando en http://localhost:${PORT}`);
});