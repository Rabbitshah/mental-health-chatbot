export default function LoadingSpinner() {
  return (
    <div
      className="flex items-center justify-center h-screen w-full"
      style={{ background: "#F7FAFD" }}
    >
      <div
        className="w-10 h-10 rounded-full border-4 border-t-transparent animate-spin"
        style={{ borderColor: "#4A90D9", borderTopColor: "transparent" }}
      />
    </div>
  );
}
