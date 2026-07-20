import { useState } from "react";

interface FeedbackProps {
  message: string
  onSubmit?: (feedback: string) => void
  onRevision?: (feedback: string) => void
}

const Feedback = ({ message, onSubmit, onRevision }: FeedbackProps) => {
  const [feedback, setFeedback] = useState<string>("")
  const [submitting, setSubmitting] = useState<boolean>(false)
  const canSubmitRevision = !submitting && feedback.trim().length > 0

  const handleSubmit = () => {
    setSubmitting(true)

    onSubmit?.(feedback)
  }
  const handleRevision = () => {
    setSubmitting(true)

    onRevision?.(feedback)
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-md p-5 max-w-2xl">
      <p className="mt-4 whitespace-pre-wrap text-slate-700">
        {message}
      </p>

      <div className="mt-5">
        <label className="mb-2 block text-sm font-medium text-slate-700">
          Revision feedback
        </label>

        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Describe what you'd like me to improve..."
          rows={5}
          className="mt-2 w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 resize-none"
        />
      </div>

      <div className="mt-6 flex justify-end gap-3">
        <button
          disabled={submitting}
          onClick={handleSubmit}
          className="cursor-pointer rounded-lg bg-green-600 px-4 py-2 font-medium text-white transition hover:bg-green-700"
        >
          ✓ Finish
        </button>

        <button
          disabled={!canSubmitRevision}
          onClick={handleRevision}
          className={`rounded-lg px-4 py-2 font-medium text-white transition cursor-pointer ${canSubmitRevision
            ? "bg-amber-600 hover:bg-amber-700"
            : "cursor-not-allowed bg-slate-300"
            }`}
        >
          ✏️ Request Revisions
        </button>
      </div>
    </div>
  )
}

export { Feedback }