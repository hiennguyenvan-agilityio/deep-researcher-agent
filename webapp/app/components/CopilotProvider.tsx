"use client";

import { CopilotKit } from "@copilotkit/react-core/v2";
import { useAuth } from "@/app/components/AuthProvider";

export function CopilotProvider({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();

  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      properties={{
        Authorization: token ? `Bearer ${token}` : undefined,
      }}
    >
      {children}
    </CopilotKit>
  );
}
