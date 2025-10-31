import React from "react";
import GaugeComponent from "react-gauge-component";

export default function RadialGauge({
    value,
    unit = "V",
    min = 0,
    max = 100,
    sizex = 300,
    sizey = 300,
    ranges = [],
    step = 0.5,
    decimals = 1,
}) {
    // Determina color según el rango definido
    const currentRange =
        ranges.find((r) => value >= r.min && value <= r.max) || {
            color: "#00BFFF",
        };

    // Limita el valor dentro del rango para que el componente no se rompa
    const safeValue = Math.min(Math.max(value, min), max);

    const tickArray = Array.from(
        { length: Math.floor((max - min) / step) + 1 },
        (_, i) => ({ value: min + i * step })
    );

    return (
        <div
            style={{
                width: sizex,
                height: sizey,
                margin: "0 auto",
                padding: "0 20px",
                overflow: "visible",
            }}
        >
            <GaugeComponent
                type="semicircle"
                minValue={min}
                maxValue={max}
                value={safeValue}
                pointer={{ hide: true }}
                arc={{
                    width: 0.25,
                    cornerRadius: 0,
                    padding: 0,
                    emptyColor: "#ccc",
                    subArcs: [
                        { limit: safeValue, color: currentRange.color },
                        { limit: max, color: "gray" },
                    ],
                }}
                labels={{
                    valueLabel: {
                        matchColorWithArc: false,
                        // mostramos el valor original aunque esté fuera del rango
                        formatTextValue: () => `${value.toFixed(decimals)} ${unit}`,
                        style: { fontSize: 50, fill: currentRange.color },
                    },
                    tickLabels: {
                        type: "outer",
                        ticks: tickArray,
                        defaultTickValueConfig: {
                            formatTextValue: (val) => `${val.toFixed(decimals)}`,
                            style: { fontSize: 16, fill: "#ccc" },
                        },
                    },
                }}
            />
        </div>
    );
}
