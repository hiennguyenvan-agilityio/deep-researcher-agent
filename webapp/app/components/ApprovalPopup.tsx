interface ApprovalPopupProps {
  message: string
  onSubmit: () => void
  onCancel: () => void
}

const ApprovalPopup = ({ message, onCancel, onSubmit }: ApprovalPopupProps) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-xl bg-white shadow-2xl border border-gray-200">
        <div className="p-6">
          <h2 className="text-xl font-semibold text-gray-900">
            Approval Required
          </h2>

          <p className="mt-3 text-sm text-gray-600 whitespace-pre-wrap">
            {message ?? "Approve this action?"}
          </p>
        </div>

        <div className="flex justify-end gap-3 border-t border-gray-100 bg-gray-50 px-6 py-4 rounded-b-xl">
          <button
            onClick={onCancel}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 cursor-pointer"
          >
            Cancel
          </button>

          <button
            onClick={onSubmit}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 cursor-pointer"
          >
            Approve
          </button>
        </div>
      </div>
    </div>
  )
}

export { ApprovalPopup }