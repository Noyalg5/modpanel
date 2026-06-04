export default function Spinner({ size = 'md' }) {
  const dim = size === 'sm' ? 'h-5 w-5' : 'h-8 w-8';
  return (
    <div className="flex justify-center items-center py-4">
      <div className={`animate-spin rounded-full ${dim} border-2 border-gray-200 border-t-blue-600`} />
    </div>
  );
}
