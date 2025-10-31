import React, { useState } from "react";
import { motion } from "framer-motion";
import Loading from "../../utils/loading";
import { apiUrl } from "../../../api/apiUrl";

export default function RunTestButton({ onClick, onResult, onStart, onError }) {
    const [loading, setLoading] = useState(false);

    const handleClick = async (retry = false) => {
        if (loading && !retry) return;

        setLoading(true);
        console.log("RunTestButton: started");

        if (onStart && !retry) onStart();

        try {
            const res = await fetch(apiUrl("/testregulator"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
            });

            if (!res.ok) {
                console.error("RunTestButton: request failed", res.status);
                if (onError) onError();
                return;
            }

            const data = await res.json();
            console.log("RunTestButton: response", data);

            const resultado = data?.resultado;
            if (resultado) {
                const allValues = [
                    ...Object.values(resultado.corrientes_1),
                    ...Object.values(resultado.corrientes_2)
                ];

                const hasNull = allValues.some((v) => v === null);

                if (hasNull) {
                    console.warn("⚠️ Se detectaron valores nulos en corrientes, repitiendo POST...");
                    setTimeout(() => handleClick(true), 1000);
                    return;
                }

                if (onResult) onResult(resultado);
            }



            if (onClick) {
                await Promise.resolve(onClick());
            } else {
                await new Promise((res) => setTimeout(res, 1200));
            }

        } catch (err) {
            console.error("RunTestButton: error in handleClick", err);
            if (onError) onError();
        } finally {
            setLoading(false);
            console.log("RunTestButton: loading false");
        }
    };

    const variants = {
        idle: { scale: 1 },
        hover: { scale: 1.05 },
        tap: { scale: 0.95 },
    };

    return (
        <motion.button
            type="button"
            onClick={() => handleClick(false)}
            disabled={loading}
            aria-busy={loading}
            initial="idle"
            whileHover={!loading ? "hover" : "idle"}
            whileTap={!loading ? "tap" : "idle"}
            variants={variants}
            className={`h-25 w-60 transition-transform text-white font-extrabold text-4xl py-4 px-10 rounded-xl shadow-lg shadow-green-800/50 hover:shadow-green-900/60 flex items-center justify-center ${loading
                    ? "bg-green-700 opacity-70 cursor-not-allowed pointer-events-none"
                    : "bg-green-600 hover:bg-green-700"
                }`}
        >
            <div className="flex items-center gap-4">
                {loading ? <Loading inline={true} /> : "RUN TEST"}
            </div>
        </motion.button>
    );
}
