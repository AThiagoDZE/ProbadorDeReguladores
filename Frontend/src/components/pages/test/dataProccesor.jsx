import React, { useEffect, useRef } from "react";

export default function DataProcessor({ resultado, onValidated }) {
    const lastProcessed = useRef(null);

    useEffect(() => {
        if (!resultado) return;

        if (JSON.stringify(resultado) === JSON.stringify(lastProcessed.current)) return;
        lastProcessed.current = resultado;

        const res = JSON.parse(JSON.stringify(resultado));
        res.validatedState = "restart";

        // --- Validaciones ---
        if (res.general_state == 3) {
            const states1 = Object.values(res.state_corrientes_1 || {});
            const okCount1 = states1.filter(s => s === "Dispositivo OK").length;
            const phaseOpenCount1 = states1.filter(s => s === "Fase abierta").length;

            const states2 = Object.values(res.state_corrientes_2 || {});
            const okCount2 = states2.filter(s => s === "Dispositivo OK").length;

            res.corrientes_2 = res.corrientes_2 || {};

            if (res.Vout > 14.75) {
                ["IaRMS", "IbRMS", "IcRMS"].forEach(key => {
                    if (typeof res.corrientes_2[key] === "number") {
                        res.corrientes_2[key] = res.corrientes_2[key] / 1000;
                    }
                });
                res.validatedState = "overvoltage";
            }
            else if (
                okCount1 >= 2 &&
                okCount2 >= 2 &&
                res.Vout < 14.15 &&
                res.Vout > 9
            ) {
                ["IaRMS", "IbRMS", "IcRMS"].forEach(key => {
                    if (typeof res.corrientes_2[key] === "number") {
                        res.corrientes_2[key] = res.corrientes_2[key] / 1000;
                    }
                });
                res.validatedState = "undervoltage";
            }
            else if (
                okCount1 === 1 &&
                phaseOpenCount1 === 2 &&
                ["IaRMS", "IbRMS", "IcRMS"].some(k => res.corrientes_2[k] > 1000)
            ) {
                const phaseMap = { dispA: "IaRMS", dispB: "IbRMS", dispC: "IcRMS" };
                Object.entries(res.state_corrientes_1).forEach(([disp, state]) => {
                    const keyRMS = phaseMap[disp];
                    if (!keyRMS) return;
                    res.corrientes_2[keyRMS] = state === "Dispositivo OK" ? 4.999 : 0;
                });
                res.Vout = 0;
                res.validatedState = "overcurrent";
            }

            else if (
                res.Vout > 0 && res.Vout < 9 &&
                ["IaRMS", "IbRMS", "IcRMS"].every(k =>
                    res.corrientes_2[k] > 0 && res.corrientes_2[k] < 500
                )
            ) {
                ["IaRMS", "IbRMS", "IcRMS"].forEach(key => res.corrientes_2[key] = 0);
                res.Vout = 0;
                res.validatedState = "disconnected";
            }

            else if (res.Vout < 10 && ["IaRMS", "IbRMS", "IcRMS"].some(k => res.corrientes_2[k] > 1000)) {
                ["IaRMS", "IbRMS", "IcRMS"].forEach(key => res.corrientes_2[key] = 0);
                res.Vout = 0;
                res.validatedState = "restart";
            }
            else {
                ["IaRMS", "IbRMS", "IcRMS"].forEach(key => res.corrientes_2[key] = 0);
                res.Vout = 0;
                res.validatedState = "restart";
            }
        }



        // general_state === 2
        else if (res.general_state === 2) {
            res.corrientes_2 = res.corrientes_2 || {};
            ["IaRMS", "IbRMS", "IcRMS"].forEach(key => {
                if (typeof res.corrientes_2[key] === "number") res.corrientes_2[key] /= 1000;
            });
            res.validatedState = "correct";
        }

        console.log("Resultado procesado:", res);

        if (onValidated) {
            onValidated({
                validatedState: res.validatedState,
                resultadoFormateado: res
            });
        }

    }, [resultado, onValidated]);

    return null;
}
