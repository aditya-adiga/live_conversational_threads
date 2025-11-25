import PropTypes from "prop-types";

export default function LoopyEditor({ selectedLoopyURL }) {
  return (
    <div className="flex-1 flex flex-col items-center">
      {/* Iframe for Loopy Editor */}
      <iframe
        src={selectedLoopyURL || "https://ncase.me/loopy/"}
        title="Loopy Model Editor"
        className="w-full h-full border-0 rounded-lg"
        allow="fullscreen; clipboard-read; clipboard-write"
      />
    </div>
  );
}

LoopyEditor.propTypes = {
  selectedLoopyURL: PropTypes.string,
};
