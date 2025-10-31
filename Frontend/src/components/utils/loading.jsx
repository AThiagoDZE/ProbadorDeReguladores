import React from "react";
import Lottie from "lottie-react";
import loadingAnimation from '../../Assets/Loading.json';

export default function Loading({ className = "max-h-40 max-w-40", inline = false }) {
    if (inline) {
        return (
            <div className={`flex items-center justify-center ${className}`}>
                <Lottie animationData={loadingAnimation} loop style={{ width: "100%", height: "100%" }} />
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center bg-slate-900 text-white h-screen w-full">
            <div className={`flex-shrink-0 ${className}`}>
                <Lottie animationData={loadingAnimation} loop style={{ width: "100%", height: "100%" }} />
            </div>
        </div>
    );
}
