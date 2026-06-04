export default function ErrorMessage({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 rounded px-3 py-2 text-sm">
      <span className="flex-1">{message}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-red-400 hover:text-red-600 leading-none text-base font-bold"
          aria-label="Dismiss"
        >
          ×
        </button>
      )}
    </div>
  );
}
