interface ErrorMessageProps {
  error: string | string[];
}

const errorStyle: React.CSSProperties = {
  color: '#c0392b',
  marginTop: '0.75rem',
};

const listStyle: React.CSSProperties = {
  margin: '0.25rem 0 0 0',
  paddingLeft: '1.25rem',
};

export function ErrorMessage({ error }: ErrorMessageProps) {
  if (Array.isArray(error)) {
    return (
      <div style={errorStyle} role="alert">
        <ul style={listStyle}>
          {error.map((msg, index) => (
            <li key={index}>{msg}</li>
          ))}
        </ul>
      </div>
    );
  }

  return (
    <p style={errorStyle} role="alert">
      {error}
    </p>
  );
}
