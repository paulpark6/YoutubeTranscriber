import { TranscriptForm } from './components/TranscriptForm';

const containerStyle: React.CSSProperties = {
  minHeight: '100vh',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'flex-start',
  padding: '3rem 1rem',
  fontFamily: 'system-ui, -apple-system, sans-serif',
  backgroundColor: '#f9f9f9',
  color: '#111',
};

const cardStyle: React.CSSProperties = {
  width: '100%',
  maxWidth: '600px',
  backgroundColor: '#fff',
  borderRadius: '8px',
  padding: '2rem',
  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
};

const headingStyle: React.CSSProperties = {
  marginTop: 0,
  marginBottom: '1.5rem',
  fontSize: '1.5rem',
  fontWeight: 700,
};

export function App() {
  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        <h1 style={headingStyle}>YouTube Transcript Downloader</h1>
        <TranscriptForm />
      </div>
    </div>
  );
}
