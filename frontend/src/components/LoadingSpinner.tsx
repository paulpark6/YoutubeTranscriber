const spinnerStyles = `
@keyframes yt-spin {
  to { transform: rotate(360deg); }
}
.yt-spinner {
  display: inline-block;
  width: 1.5rem;
  height: 1.5rem;
  border: 3px solid #ccc;
  border-top-color: #333;
  border-radius: 50%;
  animation: yt-spin 0.75s linear infinite;
  vertical-align: middle;
  margin-right: 0.5rem;
}
`;

export function LoadingSpinner() {
  return (
    <>
      <style>{spinnerStyles}</style>
      <span className="yt-spinner" role="status" aria-label="Loading" />
    </>
  );
}
