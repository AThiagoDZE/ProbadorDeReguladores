import React from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import logo from "../../assets/logo.webp";

export default function Login() {
    const navigate = useNavigate();

    const handleClick = () => {
        navigate("/home");
    };

    return (
        <motion.div
            className="flex items-center justify-center h-full"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
        >
            <motion.div
                className="bg-slate-900 rounded-2xl shadow-2xl p-10 flex flex-col items-center justify-center text-center gap-6 w-[600px]"
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.5 }}
            >
                {/* Logo */}
                <motion.img
                    src={logo}
                    alt="Logo"
                    className="w-600 h-100 object-contain drop-shadow-lg"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.3, duration: 0.5 }}
                />

                {/* Botón principal */}
                <motion.button
                    onClick={handleClick}
                    className="bg-slate-600 hover:bg-slate-700 active:scale-95 transition text-white font-bold text-2xl py-4 px-8 rounded-xl shadow-lg"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    Probador de Reguladores
                </motion.button>
            </motion.div>
        </motion.div>
    );
}
