"use client";

import { CopilotChat } from "@copilotkit/react-core/v2";
import { InterruptControler } from "@/app/components/InterruptControler"

export default function Home() {
  return (
    <>
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
