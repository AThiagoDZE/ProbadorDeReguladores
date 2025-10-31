import React from "react";
import {
    CheckCircleIcon,
    XCircleIcon,
    BoltIcon,
    ExclamationCircleIcon,
    ClockIcon,
} from "@heroicons/react/24/solid";

const STATE_STYLES = {
    correct: {
        color: "bg-green-500",
        text: "PASS",
        icon: <CheckCircleIcon className="w-12 h-12 text-white" />,
        gradient: "from-green-400 to-green-600",
    },
    failed: {
        color: "bg-red-500",
        text: "FAIL",
        icon: <XCircleIcon className="w-12 h-12 text-white" />,
        gradient: "from-red-400 to-red-600",
    },
    overvoltage: {
        color: "bg-yellow-400",
        text: "OVER VOLTAGE",
        icon: <BoltIcon className="w-12 h-12 text-white" />,
        gradient: "from-yellow-300 to-yellow-500",
    },
    undervoltage: {
        color: "bg-blue-400",
        text: "UNDER VOLTAGE",
        icon: <ExclamationCircleIcon className="w-12 h-12 text-white" />,
        gradient: "from-blue-300 to-blue-500",
    },
    overcurrent: {
        color: "bg-red-600",
        text: "OVER CURRENT",
        icon: <BoltIcon className="w-12 h-12 text-white" />,
        gradient: "from-red-500 to-red-700",
    },
    undercurrent: {
        color: "bg-purple-400",
        text: "UNDER CURRENT",
        icon: <ExclamationCircleIcon className="w-12 h-12 text-white" />,
        gradient: "from-purple-300 to-purple-500",
    },
    error: {
        color: "bg-gray-600",
        text: "GENERAL ERROR",
        icon: <XCircleIcon className="w-12 h-12 text-white" />,
        gradient: "from-gray-500 to-gray-700",
    },
    ocp: {
        color: "bg-pink-500",
        text: "OCP PROTECTION",
        icon: <BoltIcon className="w-12 h-12 text-white" />,
        gradient: "from-pink-400 to-pink-600",
    },
    idle: {
        color: "bg-slate-400",
        text: "READY TO BEGIN",
        icon: <ClockIcon className="w-12 h-12 text-white" />,
        gradient: "from-slate-300 to-slate-500",
    },
    testing: {
        color: "bg-sky-500",
        text: "TESTING...",
        icon: (
            <svg
                className="w-12 h-12 text-white animate-spin"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
            >
                <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                />
                <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                />
            </svg>
        ),
        gradient: "from-sky-400 to-sky-600",
    },
    disconnected: {
        color: "bg-gray-400",
        text: "DEVICE DISCONNECTED",
        icon: (
            <svg
                className="w-12 h-12 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
            >
                <path
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 9V5a3 3 0 013-3h6a3 3 0 013 3v4m-6 4v6m-4 4h8a2 2 0 002-2v-2H8v2a2 2 0 002 2z"
                />
                <path
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3 3l18 18"
                />
            </svg>
        ),
        gradient: "from-gray-300 to-gray-500",
    },
};


export default function StatusCard({ state = "idle" }) {
    const current = STATE_STYLES[state] || STATE_STYLES.idle;

    return (
        <div className="w-72 p-4 rounded-2xl shadow-2xl bg-slate-600 flex flex-col items-center transition-all duration-500 hover:scale-105">
            <h2 className="text-xl font-bold mb-2 text-white">TEST RESULT</h2>

            <div
                className={`w-full flex flex-col items-center justify-center p-2 rounded-xl bg-gradient-to-r ${current.gradient} shadow-lg`}
            >
                {current.icon}
                <span className="mt-4 text-white font-extrabold text-lg text-center">
                    {current.text}
                </span>
            </div>
        </div>
    );
}
