"use client";
import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from 'firebase/auth';

interface UserContextType {
    user: User | null;
    userUid: string | null;
    idToken: string | null;
    setUser: (user: User | null) => void;
    setIdToken: (token: string | null) => void;
}

const UserContext = createContext<UserContextType>({
    user: null,
    userUid: null,
    idToken: null,
    setUser: () => { },
    setIdToken: () => { },
});

export const useUser = () => useContext(UserContext);

export function UserProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [userUid, setUserUid] = useState<string | null>(null);
    const [idToken, setIdToken] = useState<string | null>(null);

    useEffect(() => {
        if (user) {
            setUserUid(user.uid);
        } else {
            setUserUid(null);
            setIdToken(null);
        }
    }, [user]);

    return (
        <UserContext.Provider value={{ user, userUid, idToken, setUser, setIdToken }}>
            {children}
        </UserContext.Provider>
    );
}
