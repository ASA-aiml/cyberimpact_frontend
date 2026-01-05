"use client";

import { useState } from "react";
import { signInWithPopup, GoogleAuthProvider, User } from "firebase/auth";
import { auth } from "../lib/firebase";

export default function Login() {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string>("");

    const handleLogin = async () => {
        const provider = new GoogleAuthProvider();
        try {
            const result = await signInWithPopup(auth, provider);
            const user = result.user;
            setUser(user);
            const idToken = await user.getIdToken();
            setToken(idToken);
            console.log("User ID Token:", idToken);
        } catch (error) {
            console.error("Error signing in:", error);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center p-4 border rounded-lg shadow-md bg-white text-black">
            <h2 className="text-xl font-bold mb-4">Login</h2>
            {user ? (
                <div className="text-center">
                    <p className="mb-2">Welcome, {user.displayName}</p>
                    <p className="text-sm text-gray-500 break-all">Token: {token.slice(0, 20)}...</p>
                </div>
            ) : (
                <button
                    onClick={handleLogin}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                >
                    Sign in with Google
                </button>
            )}
        </div>
    );
}
