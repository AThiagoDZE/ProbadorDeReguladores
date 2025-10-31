import StatusCard from "../../tools/panels/statusPanel";
import ProcessedVoltageCurrentPanel from "./gaugesProtector";
import RunTestButton from "./RunTestButton";
import DataProcessor from "./dataProccesor";
import { apiUrl } from "../../../api/apiUrl";

import { useState } from "react";

export default function RegulatorTest() {
    const [actualState, setActualState] = useState("idle");
    const [resultado, setResultado] = useState(null);
    const [resultadoProcesado, setResultadoProcesado] = useState(null);

    const minVoltage = 12.4;
    const maxVoltage = 16.4;
    const minCurr = 0;
    const maxCurr = 5;

    const voltageRanges = [
        { min: 12.4, max: 14.05, color: "#ff5100ff" },
        { min: 14.05, max: 14.25, color: "#facc15" },
        { min: 14.25, max: 14.55, color: "#22c55e" },
        { min: 14.55, max: 14.75, color: "#facc15" },
        { min: 14.75, max: 16.4, color: "#ff0000ff" },
    ];

    const currentRanges = [
        { min: 0, max: 4.5, color: "#facc15" },
        { min: 4.5, max: 5, color: "#ff0000ff" },
    ];

    const handleStart = () => {
        setResultadoProcesado({
            Vout: 0,
            corrientes_2: { IaRMS: 0, IbRMS: 0, IcRMS: 0 },
        });
        setActualState("testing");
    };

    const handleError = () => setActualState("restart");

    const handleResult = (res) => {
        console.log("Resultado recibido desde RunTestButton:", res);
        setResultado(res);
    };

    // Función callback para recibir datos procesados desde DataProcessor
    const handleProcessedData = async (validated) => {
        console.log("Datos procesados recibidos:", validated);

        if (validated?.validatedState === "restart") {
            console.log("Estado restart detectado: reiniciando prueba...");

            // Mantener el estado 'testing'
            setResultado(null);
            setResultadoProcesado(null);

            try {
                const res = await fetch(apiUrl("/testregulator"), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    credentials: "include",
                });

                if (!res.ok) throw new Error("Request failed");
                const data = await res.json();
                setResultado(data.resultado);
            } catch (err) {
                console.error("Error reiniciando prueba:", err);
                setActualState("error");
            }

            return;
        }

        // Si no es restart, actualizar estados normalmente
        if (validated?.validatedState) {
            setActualState(validated.validatedState);
        }
        if (validated?.resultadoFormateado) {
            setResultadoProcesado(validated.resultadoFormateado);
        }
    };



    return (
        <div className="flex flex-col items-center justify-center w-full h-full text-white">
            <div className="flex items-center">
                <RunTestButton
                    onStart={handleStart}
                    onResult={handleResult}
                    onError={handleError}
                />
                <div className="pb-6 pl-10">
                    <StatusCard state={actualState} />
                </div>
            </div>

            <ProcessedVoltageCurrentPanel
                resultado={resultadoProcesado}
                minVoltage={minVoltage}
                maxVoltage={maxVoltage}
                voltageRanges={voltageRanges}
                minCurr={minCurr}
                maxCurr={maxCurr}
                currentRanges={currentRanges}
            />

            <DataProcessor resultado={resultado} onValidated={handleProcessedData} />
        </div>
    );
}
