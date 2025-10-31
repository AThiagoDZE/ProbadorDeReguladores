import React from "react";
import RadialGauge from "../RadialGauge";

export default function VoltageCurrentPanel({
    voltage,
    minVoltage,
    maxVoltage,
    voltageRanges,
    currents,
    minCurr,
    maxCurr,
    currentRanges,
}) {
    return (
        <div className="flex flex-col items-center justify-center rounded-2xl shadow-2xl bg-slate-900 p-2">
            {/* Panel: gauge de voltaje */}
            <div className="text-center ">
                <h2 className="text-4xl pb-2">OUTPUT VOLTAGE</h2>
                <RadialGauge
                    value={voltage}
                    unit="V"
                    min={minVoltage}
                    max={maxVoltage}
                    sizex={500}
                    sizey={250}
                    ranges={voltageRanges}
                    decimals={1}
                />
            </div>

            {/* Panel: gauges de corriente */}
            <div className="flex justify-center gap-8 mt-4">
                {currents.map((current, index) => (
                    <div
                        key={index}
                        className="rounded-xl shadow-2xl bg-gray-800 p-2"
                    >
                        <h2 className="text-2xl text-center pb-4">
                            I ph<sub className=" text-lg text-sm align-sub font-sans"> {index + 1}</sub>
                        </h2>

                        <RadialGauge
                            value={current}
                            unit="A"
                            min={minCurr}
                            max={maxCurr}
                            sizex={200}
                            sizey={100}
                            ranges={currentRanges}
                            step={1}
                            decimals={1}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}
