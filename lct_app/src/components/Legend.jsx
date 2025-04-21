export default function Legend() {
  return (
    <div className="shadow-md rounded-lg p-2 text-xs text-gray-700 border border-gray-300 bg-white z-20">
      <h4 className="text-center font-semibold mb-1">Legend</h4>
      <div className="flex flex-col gap-1">
        <div className="flex items-center">
          <span className="w-3 h-3 bg-yellow-300 border border-yellow-500 block mr-2"></span>
          <span>Selected Node</span>
        </div>
        <div className="flex items-center">
          <span className="w-3 h-3 bg-blue-200 border border-blue-500 block mr-2"></span>
          <span>Bookmark</span>
        </div>
        <div className="flex items-center">
          <span className="w-3 h-3 bg-green-200 border border-green-500 block mr-2"></span>
          <span>Formalism</span>
        </div>
        <div className="flex items-center">
          <span className="w-3 h-3 bg-gray-300 block mr-2"></span>
          <span>Default Edge</span>
        </div>
        <div className="flex items-center">
          <span className="w-3 h-3 bg-green-500 block mr-2"></span>
          <span>Formalism Edge</span>
        </div>
        <div className="flex items-center">
          <span className="w-3 h-3 bg-orange-500 block mr-2"></span>
          <span>Selected Edge</span>
        </div>
      </div>
    </div>
  );
}
