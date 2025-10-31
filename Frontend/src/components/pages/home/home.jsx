import React, { useState } from "react";
import { motion } from "framer-motion";
import RegulatorTest from "../test/regulatorTest";
import { apiUrl } from "../../../api/apiUrl";

export default function Home() {
    const [blinkTarget, setBlinkTarget] = useState(null);

    const handleHiddenClick = async (endpoint, target) => {
        try {
            const res = await fetch(apiUrl(`/${endpoint}`), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
            });

            if (!res.ok) return;

            const data = await res.json();

            // Parpadea solo si el backend devuelve status: "ok"
            if (data.status === "ok") {
                setBlinkTarget(target);
                setTimeout(() => setBlinkTarget(null), 1200);
            }
        } catch (error) {
            console.error(`Error en ${endpoint}:`, error);
        }
    };

    const blinkClass = (target) =>
        blinkTarget === target ? "animate-[blinkGreen_0.6s_ease-in-out_2]" : "";

    return (
        <motion.main
            className="flex flex-col text-white h-full"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
        >
            {/* Título centrado */}
            <div className="w-full flex justify-center mb-8 relative">
                <h1 className="text-5xl md:text-6xl tracking-tight text-red-600 drop-shadow-[0_2px_8px_rgba(255,0,0,0.5)] text-center select-none">
                    <span
                        className={`cursor-pointer ${blinkClass("dze")}`}
                        onClick={() => handleHiddenClick("reiniciar-serial", "dze")}
                    >
                        DZE
                    </span>{" "}
                    <span
                        className={`cursor-pointer ${blinkClass("regulator")}`}
                        onClick={() => handleHiddenClick("testregulator", "regulator")}
                    >
                        REGULATOR
                    </span>{" "}
                    <span
                        className={`cursor-pointer ${blinkClass("tester")}`}
                        onClick={() => handleHiddenClick("shutdown-system", "tester")}
                    >
                        TESTER
                    </span>
                </h1>
            </div>

            {/* Contenedor principal */}
            <div>
                <RegulatorTest />
            </div>

            {/* Animación de parpadeo */}
            <style>{`
                @keyframes blinkGreen {
                    0%, 100% { color: inherit; }
                    50% { color: #22c55e; }
                }
            `}</style>
        </motion.main>
    );
}
