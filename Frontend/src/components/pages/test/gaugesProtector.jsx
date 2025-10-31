import React from "react";
import VoltageCurrentPanel from "../../tools/panels/voltageCurrPanel";

export default function ProcessedVoltageCurrentPanel({
    resultado,
    minVoltage,
    maxVoltage,
    voltageRanges,
    minCurr,
    maxCurr,
    currentRanges
}) {
    // Si no hay datos, mostramos valores en cero
    if (!resultado) {
        const zeroCurrents = [0, 0, 0];
        console.log("⚠️ Resultado vacío -> mostrando ceros");
        return (
            <VoltageCurrentPanel
                voltage={0}
                minVoltage={minVoltage}
                maxVoltage={maxVoltage}
                voltageRanges={voltageRanges}
                currents={zeroCurrents}
                minCurr={minCurr}
                maxCurr={maxCurr}
                currentRanges={currentRanges}
            />
        );
    }

    const data = resultado || {};

    console.log("Res recibida en Processed Voltage Current Panel: ", { data });

    // 🔹 Protección de Vout
    let Vout = typeof data.Vout === "number" ? data.Vout : 0;

    // Limitar máximo
    Vout = Math.min(Vout, 16.3999);

    // Redondear si está entre 7 y 12.411
    if (Vout < 12.411 && Vout > 7) {
        Vout = 12.411;
    }

    const corr2 = data.corrientes_2 || {};

    // 🔹 Limitar RMS de corrientes_2 a 4.999
    const limitRMS = (val) => {
        if (typeof val !== "number" || isNaN(val)) return 0;
        return Math.min(val, 4.999);
    };

    const currents = [
        limitRMS(corr2.IaRMS),
        limitRMS(corr2.IbRMS),
        limitRMS(corr2.IcRMS)
    ];

    console.log("✅ Recibido para graficar:", { Vout, currents });

    return (
        <VoltageCurrentPanel
            voltage={Vout}
            minVoltage={minVoltage}
            maxVoltage={maxVoltage}
            voltageRanges={voltageRanges}
            currents={currents}
            minCurr={minCurr}
            maxCurr={maxCurr}
            currentRanges={currentRanges}
        />
    );
}
