import type { ReactNode } from "react";

export default function AuthGate({ children }: { children: ReactNode }) {
  // The login gate goes here later (spec section 11); the MVP has no login.
  return <>{children}</>;
}
