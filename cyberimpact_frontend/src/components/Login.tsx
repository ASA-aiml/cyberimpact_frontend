"use client";

import { useState } from "react";
import axios from "axios";
import { signInWithPopup, GoogleAuthProvider } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { useUser } from "@/contexts/UserContext";

export default function Login() {
    const { user, setUser, setIdToken } = useUser();
    const [backendData, setBackendData] = useState<any>(null);

    const handleLogin = async () => {
        const provider = new GoogleAuthProvider();
        try {
            const result = await signInWithPopup(auth, provider);
            const idToken = await result.user.getIdToken();

            // Verify with backend
            const response = await axios.get("https://cyberimpact-frontend.onrender.com/api/verify-auth", {
                headers: {
                    Authorization: `Bearer ${idToken}`
                }
            });

            setBackendData(response.data);
            setUser(result.user); // Update context with user
            setIdToken(idToken); // Store ID token for API calls

        } catch (error) {
            console.error("Error:", error);
        }
    };

    return (
        <div className="flex flex-col items-center p-6 border rounded-xl shadow-lg bg-white text-black mb-6">
            {user ? (
                <div className="text-center space-y-4">
                    <p className="text-green-600 font-semibold">
                        {backendData?.message}
                    </p>

                    <div className="bg-gray-100 p-3 rounded-md text-left">
                        <p className="text-xs font-bold text-gray-500 uppercase">Verified UID from Backend:</p>
                        <p className="text-sm font-mono break-all">{backendData?.user?.uid}</p>
                    </div>

                    <p className="text-sm">Logged in as: <b>{user.email}</b></p>
                </div>
            ) : (
                <button
                    onClick={handleLogin}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition"
                >
                    Sign in with Google
                </button>
            )}
        </div>
    );
}
