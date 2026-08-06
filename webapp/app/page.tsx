"use client";

import { CopilotChat } from "@copilotkit/react-core/v2";
import { InterruptControler } from "@/app/components/InterruptControler"
import { AuthButton } from "@/app/components/AuthButton";

export default function Home() {
  return (
    <>
      <div className="flex justify-end p-2">
        <AuthButton />
      </div>
      <InterruptControler />
      <CopilotChat
        labels={{
          modalHeaderTitle: "Deep research assistant",
          welcomeMessageText: "What should we work on?",
        }}
      />
    </>
  );
}
